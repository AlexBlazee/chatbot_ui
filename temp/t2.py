import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize

class HybridTermMatcher:
    def __init__(self, terms_by_class, weights=None):
        """
        Initialize matcher with business terms and optional weights
        
        Parameters:
        terms_by_class: Dictionary of business terms categorized by class
        weights: Custom weights for BM25 and TF-IDF combination
        """
        self.terms_by_class = terms_by_class
        
        # Flatten all terms
        self.all_terms = [term for terms in terms_by_class.values() for term in terms]
        
        # Prepare TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.all_terms)
        
        # Prepare BM25
        self.tokenized_terms = [word_tokenize(term.lower()) for term in self.all_terms]
        self.bm25 = BM25Okapi(self.tokenized_terms)
        
        # Default weights if not provided
        self.weights = weights or {
            'bm25': 0.6,   # Primary importance to BM25
            'tfidf': 0.4   # Secondary importance to TF-IDF
        }
    
    def match(self, description, top_n=5, threshold=0.3):
        """
        Match description against business terms using hybrid approach
        
        Parameters:
        description: Input text description
        top_n: Number of top matches to return
        threshold: Minimum combined score to consider a match
        
        Returns:
        Dictionary of matched terms by class
        """
        # Tokenize description
        tokenized_description = word_tokenize(description.lower())
        
        # Calculate BM25 scores
        bm25_scores = self.bm25.get_scores(tokenized_description)
        
        # Calculate TF-IDF scores
        description_tfidf = self.tfidf_vectorizer.transform([description])
        tfidf_scores = (description_tfidf @ self.tfidf_matrix.T).toarray()[0]
        
        # Normalize scores
        bm25_normalized = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores))
        tfidf_normalized = (tfidf_scores - np.min(tfidf_scores)) / (np.max(tfidf_scores) - np.min(tfidf_scores))
        
        # Combine scores with weighted average
        combined_scores = (
            self.weights['bm25'] * bm25_normalized + 
            self.weights['tfidf'] * tfidf_normalized
        )
        
        # Organize results by class
        results = {}
        for class_name, terms in self.terms_by_class.items():
            class_matches = []
            for i, term in enumerate(terms):
                score = combined_scores[self.all_terms.index(term)]
                if score >= threshold:
                    class_matches.append((term, score))
            
            # Sort matches by score
            class_matches.sort(key=lambda x: x[1], reverse=True)
            results[class_name] = class_matches[:top_n]
        
        return results
    
    def get_recommendations(self, description, min_terms=1, max_terms=5):
        """
        Get comprehensive term recommendations
        
        Parameters:
        description: Input text description
        min_terms: Minimum number of terms to recommend
        max_terms: Maximum number of terms to recommend
        
        Returns:
        List of recommended terms with scores
        """
        # Get matches by class
        matches = self.match(description)
        
        # Flatten and sort recommendations
        all_matches = []
        for class_name, terms in matches.items():
            for term, score in terms:
                all_matches.append((term, class_name, score))
        
        # Sort by score
        all_matches.sort(key=lambda x: x[2], reverse=True)
        
        # Ensure minimum recommendations
        if len(all_matches) < min_terms:
            # Add additional terms with lower scores if needed
            pass
        
        return all_matches[:max_terms]

# Example usage
if __name__ == "__main__":
    terms_by_class = {
        "CHSI": ["Customer Health Score", "Client Satisfaction", "Health Metrics"],
        "BP": ["Business Process", "Workflow Optimization", "Operational Excellence"],
        "EU": ["End User", "User Experience", "Customer Journey"]
    }
    
    matcher = HybridTermMatcher(terms_by_class)
    
    description = "Improving customer satisfaction through better business processes"
    
    recommendations = matcher.get_recommendations(description)
    
    print("Recommendations:")
    for term, class_name, score in recommendations:
        print(f"{term} ({class_name}): {score:.2f}")