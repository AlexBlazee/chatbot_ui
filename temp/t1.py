import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

class BusinessTermMatcher:
    def __init__(self, terms_by_class, threshold=0.5):
        """
        Initialize the matcher with business terms by class.
        
        Parameters:
        terms_by_class: dict - Dictionary with class names as keys and lists of terms as values
        threshold: float - Minimum similarity score to consider a match
        """
        self.terms_by_class = terms_by_class
        self.threshold = threshold
        self.all_terms = [term for terms in terms_by_class.values() for term in terms]
        
        # Initialize models
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.all_terms)
        
        # Initialize sentence transformer
        # self.transformer_model = SentenceTransformer('all-MiniLM-L6-v2')
        # self.term_embeddings = {term: self.transformer_model.encode(term) 
        #                        for class_name, terms in terms_by_class.items() 
        #                        for term in terms}
        
        # Prepare for BM25
        self.tokenized_terms = {term: word_tokenize(term.lower()) 
                              for term in self.all_terms}
        corpus = list(self.tokenized_terms.values())
        self.bm25 = BM25Okapi(corpus)
        
        # Map terms to their indices for BM25
        self.term_to_idx = {term: i for i, term in enumerate(self.all_terms)}
        
    def preprocess_text(self, text):
        """Clean and normalize the text."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tfidf_similarity(self, description):
        """Calculate TF-IDF based similarity between description and terms."""
        # Add the description to the vocabulary without affecting the model
        description_vector = self.tfidf_vectorizer.transform([description])
        
        # Calculate cosine similarity
        similarity_scores = (description_vector @ self.tfidf_matrix.T).toarray()[0]
        
        # Create term-score mapping
        return {term: similarity_scores[i] for i, term in enumerate(self.all_terms)}
    
    # def semantic_similarity(self, description):
    #     """Calculate semantic similarity using transformer models."""
    #     description_embedding = self.transformer_model.encode(description)
        
    #     similarities = {}
    #     for term, term_embedding in self.term_embeddings.items():
    #         similarity = np.dot(description_embedding, term_embedding) / (
    #             np.linalg.norm(description_embedding) * np.linalg.norm(term_embedding)
    #         )
    #         similarities[term] = similarity
            
    #     return similarities
    
    def bm25_similarity(self, description):
        """Calculate BM25 similarity scores."""
        tokenized_description = word_tokenize(description.lower())
        term_scores = self.bm25.get_scores(tokenized_description)
        
        return {term: term_scores[self.term_to_idx[term]] for term in self.all_terms}
    
    def exact_match_bonus(self, description):
        """Add bonus for exact matches."""
        description_lower = description.lower()
        matches = {}
        
        for term in self.all_terms:
            # Add a higher score for exact match
            if term.lower() in description_lower:
                # Calculate the frequency of the term in the description
                term_freq = description_lower.count(term.lower())
                matches[term] = min(1.0, 0.3 + (0.1 * term_freq))
            else:
                matches[term] = 0.0
                
        return matches
    
    def match(self, description, top_n=5, weights=None):
        """
        Match the description against business terms.
        
        Parameters:
        description: str - The description text
        top_n: int - Number of top matches to return per class
        weights: dict - Optional weights for different methods 
                       (default: tfidf=0.25, semantic=0.4, bm25=0.25, exact=0.1)
        
        Returns:
        dict - Dictionary with class names as keys and lists of (term, score) tuples as values
        """
        if weights is None:
            weights = {
                'tfidf': 0.25,
                'semantic': 0.4,
                'bm25': 0.25,
                'exact': 0.1
            }
            
        # Normalize weights
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Preprocess description
        processed_description = self.preprocess_text(description)
        
        # Get scores from different methods
        tfidf_scores = self.tfidf_similarity(processed_description)
        # semantic_scores = self.semantic_similarity(processed_description)
        bm25_scores = self.bm25_similarity(processed_description)
        exact_scores = self.exact_match_bonus(processed_description)
        
        # Normalize scores within each method
        methods = {
            'tfidf': tfidf_scores,
            # 'semantic': semantic_scores,
            'bm25': bm25_scores,
            'exact': exact_scores
        }
        
        # Calculate combined scores
        combined_scores = {}
        for term in self.all_terms:
            combined_scores[term] = sum(
                normalized_weights[method_name] * method_scores.get(term, 0)
                for method_name, method_scores in methods.items()
            )
        
        # Filter by threshold and group by class
        results = {}
        for class_name, terms in self.terms_by_class.items():
            results[class_name] = [
                (term, combined_scores[term]) 
                for term in terms 
                if combined_scores[term] >= self.threshold
            ]
            results[class_name].sort(key=lambda x: x[1], reverse=True)
            results[class_name] = results[class_name][:top_n]            
        return results
    
    def get_recommendations(self, description, min_terms=1, max_terms=5):
        """
        Get term recommendations across all classes.
        
        Parameters:
        description: str - The description text
        min_terms: int - Minimum number of terms to recommend
        max_terms: int - Maximum number of terms to recommend
        
        Returns:
        list - List of (term, class, score) tuples sorted by relevance
        """
        matches = self.match(description)
        
        # Flatten results across classes
        all_matches = []
        for class_name, terms in matches.items():
            for term, score in terms:
                all_matches.append((term, class_name, score))
                
        # Sort by score
        all_matches.sort(key=lambda x: x[2], reverse=True)
        
        # Ensure minimum number of recommendations
        if len(all_matches) < min_terms:
            # Add more terms even below threshold
            remaining_scores = {}
            for term in self.all_terms:
                # Skip terms already in recommendations
                if any(term == match[0] for match in all_matches):
                    continue
                    
                # Find the class this term belongs to
                # for class_name, terms in self.terms_by_class.items():
                #     if term in terms:
                #         processed_description = self.preprocess_text(description)
                #         # semantic_score = self.semantic_similarity(processed_description).get(term, 0)
                #         remaining_scores[(term, class_name)] = semantic_score
                #         break
            
            # Get top remaining terms
            top_remaining = sorted(remaining_scores.items(), key=lambda x: x[1], reverse=True)
            for (term, class_name), score in top_remaining:
                if len(all_matches) >= min_terms:
                    break
                all_matches.append((term, class_name, score))
        
        # Limit to max_terms
        return all_matches[:max_terms]

# Example usage
if __name__ == "__main__":
    # Example data
    terms_by_class = {
        "CHSI": ["Customer Health Score Index", "Client Satisfaction", "Health Metrics", "Customer Retention"],
        "BP": ["Business Process", "Workflow Optimization", "Operational Excellence", "Process Automation"],
        "EU": ["End User", "User Experience", "Customer Journey", "User Interface"]
    }
    
    matcher = BusinessTermMatcher(terms_by_class, threshold=0.3)
    
    # Example description
    description = "We need to improve our customer health monitoring system to better track client satisfaction and reduce churn."
    
    # Get recommendations
    recommendations = matcher.get_recommendations(description, max_terms=3)
    
    print("Top recommendations:")
    for term, class_name, score in recommendations:
        print(f"{term} ({class_name}): {score:.2f}")