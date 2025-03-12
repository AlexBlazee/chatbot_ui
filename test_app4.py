from dataclasses import dataclass, field
from typing import Literal, List, Optional, Any
import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime
from pydantic import BaseModel, Field
import pandas as pd

BASE_URL = "http://localhost:8000"
g_user_id = "temp"

class BotMessage(BaseModel):
    main_text: Optional[str] = None
    buttons: Optional[List[str]] = None
    text_area: Optional[str] = None
    text_field: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    enable_text: Optional[bool] = False
    enable_text_area: Optional[bool] = False
    enable_calender: Optional[bool] = False
    enable_attachment: Optional[bool] = False
    enable_records: Optional[bool] = False
    enable_filter: Optional[bool] = False
    filter_data: Optional[List[str]] = None

class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    sender: str
    state: str
    messages: List[BotMessage] = []
    callable: Optional[bool] = False

@dataclass
class Message:
    """Class for keeping track of a chat message."""
    origin: Literal["human", "ai"]
    message: str
    buttons: Optional[List[str]] = None
    enable_text: bool = True
    enable_text_area: bool = False
    enable_calender: bool = False
    enable_attachment: bool = False
    buttons_disabled: bool = False
    enable_records: bool = False
    records_data: Optional[Any] = None
    enable_filter: bool = False
    filter_data: List[str] = field(default_factory=list)
    filter_selections: List[str] = field(default_factory=list)
    filter_submitted: bool = False

def load_css():
    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

def process_state(human_prompt=None, files=None, data=None):
    # Example response with filter data
    if human_prompt and "filter" in human_prompt.lower():
        response = {
            'session_id': "TEMP_SESSION",
            'user_id': 'temp',
            'sender': 'bot',
            'state': 'FILTER_RESP',
            'messages': [{
                'main_text': 'Please filter these items:',
                'enable_filter': True,
                'filter_data': ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta", "Project Epsilon"],
                'buttons': [],
                'text_area': None,
                'text_field': None,
                'data': None,
                'timestamp': datetime.now(),
                'enable_text': False,
                'enable_text_area': False,
                'enable_calender': False,
                'enable_attachment': False,
                'enable_records': False
            }]
        }
        return response
    
    # Example response with records data
    if human_prompt and "show records" in human_prompt.lower():
        # Mock records data
        mock_records = [
            {"Reporting DCID": 12345, "Phase": "Planning", "Data Owner": "John Doe", 
             "Status Label": "Active", "Created Date": "2024-03-01"},
            {"Reporting DCID": 12346, "Phase": "Execution", "Data Owner": "Jane Smith", 
             "Status Label": "Pending", "Created Date": "2024-03-02"},
            {"Reporting DCID": 12347, "Phase": "Review", "Data Owner": "Bob Johnson", 
             "Status Label": "Completed", "Created Date": "2024-03-03"},
            {"Reporting DCID": 12348, "Phase": "Closed", "Data Owner": "Alice Brown", 
             "Status Label": "Archived", "Created Date": "2024-03-04"},
            {"Reporting DCID": 12349, "Phase": "Planning", "Data Owner": "Charlie Green", 
             "Status Label": "Active", "Created Date": "2024-03-05"}
        ]
        
        response = {
            'session_id': "TEMP_SESSION",
            'user_id': 'temp',
            'sender': 'bot',
            'state': 'RECORDS_RESP',
            'messages': [
                {
                    'main_text': 'Here are the records you requested:',
                    'buttons': [],
                    'text_area': None,
                    'text_field': None,
                    'data': mock_records,
                    'timestamp': datetime.now(),
                    'enable_text': True,
                    'enable_text_area': False,
                    'enable_calender': False,
                    'enable_attachment': False,
                    'enable_records': True
                }
            ]
        }
        return response
    
    # If filter selections were submitted
    if data and "filters" in data:
        response = {
            'session_id': "TEMP_SESSION",
            'user_id': 'temp',
            'sender': 'bot',
            'state': 'FILTER_CONFIRMATION',
            'messages': [{
                'main_text': f"You've filtered by: {', '.join(data['filters'])}. What would you like to do next?",
                'buttons': ['View Details', 'Export Data', 'Cancel'],
                'text_area': None,
                'text_field': None,
                'data': None,
                'timestamp': datetime.now(),
                'enable_text': True,
                'enable_text_area': False,
                'enable_calender': False,
                'enable_attachment': False,
                'enable_records': False,
                'enable_filter': False
            }]
        }
        return response
    
    # Default response for other cases
    response = {
        'session_id': "TEMP_SESSION",
        'user_id': 'temp',
        'sender': 'bot',
        'state': 'INITIAL_RESP',
        'messages': [
            {
                'main_text': 'Hello! How can I assist you?',
                'buttons': ['Check status', 'Submit concern', 'Show Records', 'Filter Data'],
                'text_area': None,
                'text_field': None,
                'data': None,
                'timestamp': datetime.now(),
                'enable_text': False,
                'enable_text_area': False,
                'enable_calender': False,
                'enable_attachment': True,
                'enable_records': False,
                'enable_filter': False
            }
        ]
    }
    return response

def start_chat(user_id):
    st.session_state.session_id = "TEMP_SESSION"
    st.session_state.state = "INITIAL"

def initialize_session_state():
    required_states = {
        "session_id": g_user_id,
        "state": "INITIAL",
        "history": [],
        "user_input": "",
        "text_area_input": "",
        "selected_date": None,
        "uploaded_files": None,
        "first_message_sent": False,
        "last_interaction_index": -1
    }
    for key, value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

def on_button_click(button_text, message_index):
    # Disable buttons for this message
    st.session_state.history[message_index].buttons_disabled = True
    st.session_state.last_interaction_index = message_index
    
    # Add user's selection to history
    st.session_state.history.append(Message("human", f"{button_text}"))
    
    # Process response
    response = process_state(button_text)
    handle_bot_response(response)

def on_text_submit(message_index):
    if st.session_state.user_input:
        st.session_state.last_interaction_index = message_index
        st.session_state.history.append(Message("human", st.session_state.user_input))
        response = process_state(st.session_state.user_input)
        handle_bot_response(response)
        st.session_state.user_input = ""

def on_filter_next(message_index):
    filter_key = f"filter_selections_{message_index}"
    
    if st.session_state.get(filter_key) and len(st.session_state[filter_key]) > 0:
        # Get the selected filters
        selections = st.session_state[filter_key]
        
        # Update the message to store the selections and mark as submitted
        st.session_state.history[message_index].filter_selections = selections
        st.session_state.history[message_index].filter_submitted = True
        
        # Update the last interaction index to prevent re-rendering
        st.session_state.last_interaction_index = message_index
        
        # Add user message showing selections
        st.session_state.history.append(Message(
            "human", 
            f"Selected filters: {', '.join(selections)}"
        ))
        
        # Process the response with the filter data
        response = process_state(data={"filters": selections})
        handle_bot_response(response)
    else:
        st.error("Please select at least one filter option")

def on_date_next_click(index):
    date_key = f"date_{index}"
    if st.session_state.get(date_key):
        selected_date = st.session_state[date_key]
        st.session_state[f"submitted_date_{index}"] = selected_date
        st.session_state.history[index].enable_calender = False
        st.session_state.last_interaction_index = index
        
        st.session_state.history.append(
            Message("human", f"Selected date: {selected_date}")
        )
        response = process_state(data={"date": str(selected_date)})
        handle_bot_response(response)
    else:
        st.error("Please select a date")

def on_text_area_submit():
    last_text_area_index = None
    for i, msg in enumerate(st.session_state.history):
        if msg.origin == "ai" and msg.enable_text_area:
            last_text_area_index = i
    
    if last_text_area_index is not None:
        text_input = st.session_state.get(f"text_area_{last_text_area_index}")
        if text_input:
            st.session_state[f"submitted_text_{last_text_area_index}"] = text_input
            st.session_state.history[last_text_area_index].enable_text_area = False
            st.session_state.last_interaction_index = last_text_area_index
            
            st.session_state.history.append(
                Message("human", f"Submitted: {text_input}")
            )
            response = process_state(text_input)
            handle_bot_response(response)

def on_file_upload(message_index):
    files_key = f"files_{message_index}"
    submitted_key = f"files_submitted_{message_index}"
    st.session_state.last_interaction_index = message_index
    
    if st.session_state.get(files_key):
        # Store uploaded files in separate session state
        st.session_state[submitted_key] = st.session_state[files_key]
        
        # Process files and update chat
        file_names = [file.name for file in st.session_state[submitted_key]]
        st.session_state.history.append(Message("human", f"Uploaded files: {', '.join(file_names)}"))
        response = process_state(files=file_names)
        handle_bot_response(response)
        
        # Set a flag to indicate files have been processed
        st.session_state[f"files_processed_{message_index}"] = True
    else:
        st.error("Please upload files first.")

def handle_bot_response(response):
    if 'messages' in response:
        for msg in response['messages']:
            bot_message = Message(
                origin="ai",
                message=msg.get('main_text', ''),
                buttons=msg.get('buttons'),
                enable_text=msg.get('enable_text', False),
                enable_text_area=msg.get('enable_text_area', False),
                enable_calender=msg.get('enable_calender', False),
                enable_attachment=msg.get('enable_attachment', False),
                enable_records=msg.get('enable_records', False),
                records_data=msg.get('data'),
                enable_filter=msg.get('enable_filter', False),
                filter_data=msg.get('filter_data', [])
            )
            st.session_state.history.append(bot_message)

def main():
    load_css()
    initialize_session_state()
    st.title("Interactive Chatbot 🤖")

    if not st.session_state.first_message_sent:
        response = process_state()
        handle_bot_response(response)
        st.session_state.first_message_sent = True

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, chat in enumerate(st.session_state.history):
            # Message bubbles
            if chat.message:
                st.markdown(f"""
                <div class="chat-row {'row-reverse' if chat.origin == 'human' else ''}">
                    <img class="chat-icon" src="static/{'user_icon.png' if chat.origin == 'human' else 'ai_icon.png'}" width=32 height=32>
                    <div class="chat-bubble {'human-bubble' if chat.origin == 'human' else 'ai-bubble'}">
                        &#8203;{chat.message}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Interactive elements
            if chat.origin == "ai":
                # Buttons
                if chat.buttons and not chat.buttons_disabled and i > st.session_state.last_interaction_index:
                    cols = st.columns(len(chat.buttons))
                    for idx, btn_text in enumerate(chat.buttons):
                        cols[idx].button(btn_text, key=f"btn_{i}_{idx}", 
                                      on_click=on_button_click, args=(btn_text, i))
                
                # Calendar
                if chat.enable_calender and i > st.session_state.last_interaction_index:
                    st.write("Select a date")  
                    cols = st.columns([4, 2])
                    with cols[0]:
                        st.date_input("", key=f"date_{i}", value=None, label_visibility="collapsed")
                    with cols[1]:
                        st.button("Next", key=f"date_btn_{i}", on_click=on_date_next_click, args=(i,))

                if f"submitted_date_{i}" in st.session_state:
                    st.info(f"Selected Date: {st.session_state[f'submitted_date_{i}']}")

                # Display file uploader if enabled
                if chat.enable_attachment and i > st.session_state.last_interaction_index:
                    files_processed = st.session_state.get(f"files_processed_{i}", False)
                        
                    if not files_processed:
                        cols = st.columns([4, 1])
                        with cols[0]:
                            st.file_uploader(
                                "Upload files",
                                accept_multiple_files=True,
                                key=f"files_{i}",
                                label_visibility="collapsed"
                            )
                            
                        with cols[1]:
                            st.button(
                                "Next Step",
                                key=f"file_btn_{i}",
                                on_click=on_file_upload,
                                args=(i,),
                                help="Click after uploading files to proceed"
                            )
                    else:
                        # Show already submitted files
                        if f"files_submitted_{i}" in st.session_state:
                            file_names = [file.name for file in st.session_state[f"files_submitted_{i}"]]
                            st.success(f"Files uploaded: {', '.join(file_names)}")
                
                # Text Area
                if chat.enable_text_area and i > st.session_state.last_interaction_index:
                    with st.form(key=f"text_form_{i}", clear_on_submit=True):
                        st.text_area("Your response", key=f"text_area_{i}")
                        st.form_submit_button("Submit", on_click=on_text_area_submit)
                
                # Display records
                if chat.enable_records and chat.records_data:
                    st.subheader("Records Data")
                    records_df = pd.DataFrame(chat.records_data)
                    
                    st.dataframe(
                        records_df,
                        column_config={
                            "Reporting DCID": st.column_config.NumberColumn("Reporting DCID"),
                            "Phase": st.column_config.TextColumn("Phase"),
                            "Data Owner": st.column_config.TextColumn("Data Owner"),
                            "Status Label": st.column_config.TextColumn("Status Label"),
                            "Created Date": st.column_config.DateColumn("Created Date")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                # Show submitted content
                if f"submitted_text_{i}" in st.session_state:
                    with st.container(): 
                        with st.expander("Submitted Text"):
                            st.write(st.session_state[f"submitted_text_{i}"])
                
                # Filter UI
                if chat.enable_filter and chat.filter_data:
                    # Check if this filter has been submitted already
                    filter_submitted = getattr(chat, 'filter_submitted', False)
                    
                    if not filter_submitted and i > st.session_state.last_interaction_index:
                        st.subheader("Filter Selection")
                        
                        # Use multiselect for filter selection
                        st.multiselect(
                            "Select items to filter:",
                            options=chat.filter_data,
                            default=chat.filter_selections,
                            key=f"filter_selections_{i}"
                        )
                        
                        # Button to submit filter selections
                        st.button(
                            "Apply Filters", 
                            key=f"filter_next_{i}", 
                            on_click=on_filter_next, 
                            args=(i,)
                        )
                    else:
                        # If already submitted, just show the selections
                        if chat.filter_selections:
                            st.success(f"Filters applied: {', '.join(chat.filter_selections)}")

    # Text input at bottom
    if st.session_state.history and \
       st.session_state.history[-1].origin == "ai" and \
       st.session_state.history[-1].enable_text:
        with st.form("chat_input"):
            cols = st.columns([6, 1])
            cols[0].text_input("Message", key="user_input", value="",
                             label_visibility="collapsed")
            cols[1].form_submit_button("Submit", on_click=on_text_submit, args=(len(st.session_state.history)-1,))

    # JavaScript to handle Enter key for form submission
    components.html("""
    <script>
    const streamlitDoc = window.parent.document;

    const buttons = Array.from(
        streamlitDoc.querySelectorAll('.stButton > button')
    );
    const submitButton = buttons.find(
        el => el.innerText === 'Submit'
    );

    if (submitButton) {
        streamlitDoc.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey && document.activeElement.tagName !== 'TEXTAREA') {
                submitButton.click();
            }
        });
    }
    </script>
    """, 
        height=0,
        width=0,
    )


if __name__ == "__main__":
    main()