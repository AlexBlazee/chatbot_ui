from dataclasses import dataclass, field
from typing import Literal, List, Optional, Any, Dict
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


class DCIDForm(BaseModel):
    data_concern : str = None 
    source : str = None
    detected_csi_application: Optional[List[str]] = None
    euc: Optional[str] = None
    impacted_business_process : Optional[List[str]] = None
    impacted_data_elements: Optional[List[str]] = None
    frequency : str = None
    detected_date: datetime = None
    sample_data_attachements : Optional[List[str]] = []
    primary_contact: str = None
    on_behalf_of: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    sender: str
    state: str
    messages: List[BotMessage] = []
    callable: Optional[bool] = False

# @dataclass
# class Message:
#     """Class for keeping track of a chat message."""
#     origin: Literal["human", "ai"]
#     message: str
#     buttons: Optional[List[str]] = None
#     enable_text: bool = True
#     enable_text_area: bool = False
#     enable_calender: bool = False
#     enable_attachment: bool = False
#     buttons_disabled: bool = False
#     enable_records: bool = False
#     records_data: Optional[Any] = None
#     enable_filter: bool = False
#     filter_data: List[str] = field(default_factory=list)
#     filter_selections: List[str] = field(default_factory=list)
#     filter_submitted: bool = False

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
    # New form-related fields
    enable_form: bool = False
    form_data: Optional[Dict] = None
    mandatory_fields: Optional[Dict] = None
    editable_fields: Optional[Dict] = None
    filter_config: Optional[Dict] = None

def load_css():
    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

def process_state(human_prompt=None, files=None, data=None):
    # Default response if no specific condition is met
    default_response = {
        'session_id': "TEMP_SESSION",
        'user_id': 'temp',
        'sender': 'bot',
        'state': 'INITIAL_RESP',
        'messages': [
            {
                'main_text': 'Hello! How can I assist you?',
                'buttons': ['Check status', 'Submit concern', 'Show Records', 'Filter Data', 'Show Form'],
                'text_area': None,
                'text_field': None,
                'data': None,
                'timestamp': datetime.now(),
                'enable_text': False,
                'enable_text_area': False,
                'enable_calender': False,
                'enable_attachment': True,
                'enable_records': False,
                'enable_filter': False,
                'enable_form': False
            }
        ]
    }

    if human_prompt and "show form" in human_prompt.lower():
        # Your form data and metadata
        sample_data = {
            'data_concern': " The description",
            'source': 'The Source',
            'detected_csi_application': ['D book'],
            'euc': None,
            'impacted_business_process': None,
            'impacted_data_elements': ['Market'],
            'frequency': 'Isolated Instance',
            'detected_date': '2025-03-17',
            'sample_data_attachements': ['Screenshot 2025-01-14 121747.png', 'Screenshot 2025-01-23 154637.png'],
            'primary_contact': ['SOEID1'],
            'on_behalf_of': None,
        }
        
        mandatory_config = {
            'data_concern' : True ,
            'source' : True,
            'detected_csi_application': False,
            'euc': False,
            'impacted_business_process' : False,
            'impacted_data_elements' : False,
            'frequency' : True,
            'detected_date': True,
            'sample_data_attachements' : False,
            'primary_contact': True,
            'on_behalf_of': False,
        }

        editable_config = {
            'data_concern' : False,
            'source' : True,
            'detected_csi_application': True,
            'euc': True,
            'impacted_business_process' : True,
            'impacted_data_elements' : True,
            'frequency' : True,
            'detected_date': True,
            'sample_data_attachements' : True,
            'primary_contact': True,
            'on_behalf_of': True,
        }

        # modify above based on the source type
        filter_data = {
            'data_concern': None,
            'source': ['A' , 'B' , 'C'],
            'detected_csi_application': ['A1' , 'A2' , 'A3' , 'A4' , 'A5'],
            'euc': ['C1' , 'C2' , 'C3'],
            'impacted_business_process' :  ['B1' ,'B2' , 'B3' , 'B4'],
            'impacted_data_elements' : ['D1' , 'D2' , 'D3' , 'D4'],
            'frequency' : ['I','O','F'],
            'detected_date': None,# open calender , user can select date,
            'sample_data_attachements' : None , # open file uploader functionality so user can upload files 
            'primary_contact': ['S1' ,'S2' ,'S3'],
            'on_behalf_of': ['S1','S2','S3']
        }

        filter_config = {
            'data_concern' : None,
            'source' : 'single',
            'detected_csi_application': 'single',
            'euc': 'single',
            'impacted_business_process' : 'multi',
            'impacted_data_elements' : 'multi',
            'frequency' : 'single',
            'detected_date': None, # since its calender 
            'sample_data_attachements' : None, # since its file uploader
            'primary_contact': 'single',
            'on_behalf_of': 'single',
        }

        response = {
            'session_id': "TEMP_SESSION",
            'user_id': 'temp',
            'sender': 'bot',
            'state': 'FORM_RESP',
            'messages': [{
                'main_text': 'Here is the form:',
                'data': {
                    'form_data': sample_data, # The current data the form holds 
                    'mandatory_fields' : mandatory_config, # these the fields that should have some value and cannot be empty , True means mandatory , False means Optional
                    'editable_fields': editable_config, # These fields show if the config is editable or not , if True its Editable , if not its not editable
                    'filter_data' : filter_data, #  This is used to filter data , when None , then filter should not be applied , when a list of values is given then filter option should be given to the user
                    'filter_config' : filter_config # From the above filter option, it will give the option to either select a single option or select multipl options
                },
                'buttons': ['Submit Form'],
                'text_area': None,
                'text_field': None,
                'timestamp': datetime.now(),
                'enable_text': False,
                'enable_text_area': False,
                'enable_calender': False,
                'enable_attachment': False,
                'enable_records': False,
                'enable_filter': False,
                'enable_form' : True, # When this is True , the form gets enabled to display and edit. 
                }]
            }
        return response

    # For form submitted data
    if human_prompt == "form_submitted" and data and "form_data" in data:
        response = {
            'session_id': "TEMP_SESSION",
            'user_id': 'temp',
            'sender': 'bot',
            'state': 'FORM_SUBMITTED',
            'messages': [{
                'main_text': 'Form submitted successfully! Thank you for your input.',
                'buttons': ['Check status', 'Submit concern', 'Show Records'],
                'text_area': None,
                'text_field': None,
                'data': None,
                'timestamp': datetime.now(),
                'enable_text': True,
                'enable_text_area': False,
                'enable_calender': False,
                'enable_attachment': False,
                'enable_records': False,
                'enable_filter': False,
                'enable_form': False
            }]
        }
        return response

    # Return default response for all other cases
    return default_response

def display_form(form_data, mandatory_fields, editable_fields, filter_data, filter_config, message_index):
    """Display and handle the DCID form with editing capabilities"""
    st.markdown("### DCID Form")
    
    # Safety checks for None values
    form_data = form_data or {}
    mandatory_fields = mandatory_fields or {}
    editable_fields = editable_fields or {}
    filter_data = filter_data or {}
    filter_config = filter_config or {}
    
    # Initialize form state if not already in session state
    form_state_key = f"form_state_{message_index}"
    if form_state_key not in st.session_state:
        st.session_state[form_state_key] = form_data.copy()
    
    # Track if any field is in edit mode
    edit_mode_key = f"edit_mode_{message_index}"
    if edit_mode_key not in st.session_state:
        st.session_state[edit_mode_key] = {}
    
    # Build the form UI
    with st.container():
        # Use a table-like layout for the form
        for field_name in form_data.keys():
            field_value = st.session_state[form_state_key].get(field_name, form_data.get(field_name))
            is_mandatory = mandatory_fields.get(field_name, False)
            is_editable = editable_fields.get(field_name, False)
            field_filters = filter_data.get(field_name)
            filter_type = filter_config.get(field_name)
            
            # Display row with field name and value/editor
            col1, col2, col3 = st.columns([2, 5, 1])
            
            # Field label with mandatory indicator
            with col1:
                label = field_name.replace('_', ' ').title()
                if is_mandatory:
                    st.markdown(f"**{label}** <span style='color:red'>*</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**{label}**")
            
            # Field value or editor
            with col2:
                field_key = f"{field_name}_{message_index}"
                edit_key = f"{field_name}_edit_{message_index}"
                
                # Check if field is in edit mode
                is_in_edit_mode = st.session_state[edit_mode_key].get(field_name, False)
                
                if is_in_edit_mode and is_editable:
                    # Different input types based on field and filter configuration
                    if field_name == 'detected_date':
                        # Calendar input for date
                        date_value = None
                        if field_value and isinstance(field_value, str):
                            try:
                                date_value = datetime.strptime(field_value, '%Y-%m-%d').date()
                            except ValueError:
                                date_value = None
                        
                        selected_date = st.date_input(
                            "Select date",
                            value=date_value,
                            key=field_key,
                            label_visibility="collapsed"
                        )
                        # Update form state immediately
                        st.session_state[form_state_key][field_name] = selected_date.strftime('%Y-%m-%d')
                        
                    elif field_name == 'sample_data_attachements':
                        # File uploader for attachments
                        uploaded_files = st.file_uploader(
                            "Upload attachments",
                            accept_multiple_files=True,
                            key=field_key,
                            label_visibility="collapsed"
                        )
                        if uploaded_files:
                            file_names = [file.name for file in uploaded_files]
                            # Update form state immediately
                            st.session_state[form_state_key][field_name] = file_names
                            
                    elif field_filters is not None:
                        # Dropdown or multiselect based on filter config
                        if filter_type == 'single':
                            # Single select dropdown
                            default_idx = 0
                            if field_value in field_filters:
                                default_idx = field_filters.index(field_value)
                            
                            selected = st.selectbox(
                                "Select value",
                                options=field_filters,
                                index=default_idx,
                                key=field_key,
                                label_visibility="collapsed"
                            )
                            # Update form state immediately
                            st.session_state[form_state_key][field_name] = selected
                        elif filter_type == 'multi':
                            # Multi-select
                            default_values = []
                            if isinstance(field_value, list) and field_value:
                                # Filter to only include values that exist in field_filters
                                default_values = [v for v in field_value if v in field_filters]
                            
                            selected = st.multiselect(
                                "Select values",
                                options=field_filters,
                                default=default_values,
                                key=field_key,
                                label_visibility="collapsed"
                            )
                            # Update form state immediately
                            st.session_state[form_state_key][field_name] = selected
                    else:
                        # Text input for other fields
                        default_text = ""
                        if field_value is not None:
                            default_text = field_value if isinstance(field_value, str) else str(field_value)
                        
                        if field_name == 'data_concern':
                            # Use text area for data concern as it's usually longer
                            input_value = st.text_area(
                                "Enter value",
                                value=default_text,
                                key=field_key,
                                label_visibility="collapsed",
                                on_change=lambda: st.session_state.update({
                                    form_state_key: {
                                        **st.session_state[form_state_key],
                                        field_name: st.session_state[field_key]
                                    }
                                })
                            )
                        else:
                            input_value = st.text_input(
                                "Enter value",
                                value=default_text,
                                key=field_key,
                                label_visibility="collapsed"
                            )
                        # Update form state immediately
                        st.session_state[form_state_key][field_name] = input_value
                    
                    # Save/Cancel buttons for edit mode
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.button("Save", key=f"save_{field_key}"):
                            # Exit edit mode - values already saved
                            st.session_state[edit_mode_key][field_name] = False
                            st.rerun()
                    
                    with cancel_col:
                        if st.button("Cancel", key=f"cancel_{field_key}"):
                            # Revert to original value
                            if field_name in form_data:
                                st.session_state[form_state_key][field_name] = form_data[field_name]
                            # Exit edit mode
                            st.session_state[edit_mode_key][field_name] = False
                            st.rerun()
                else:
                    # Display value in view mode
                    display_value = field_value
                    
                    # Format display based on field type
                    if display_value is None:
                        st.write("None")
                    elif field_name == 'detected_date' and display_value:
                        st.write(display_value)
                    elif field_name == 'sample_data_attachements' and display_value:
                        if isinstance(display_value, list):
                            st.write(", ".join(display_value))
                        else:
                            st.write(display_value)
                    elif isinstance(display_value, list):
                        st.write(", ".join(map(str, display_value)) if display_value else "None")
                    else:
                        st.write(display_value)
            
            # Edit button for editable fields
            with col3:
                if is_editable and not is_in_edit_mode:
                    if st.button("Edit", key=edit_key):
                        st.session_state[edit_mode_key][field_name] = True
                        st.rerun()
                elif not is_editable:
                    st.write("")
            
            st.divider()
    
    # Submit button for the whole form
    if st.button("Submit Changes", key=f"submit_form_{message_index}"):
        # Validate form before submission
        form_is_valid = True
        validation_messages = []
        
        # Check mandatory fields
        for field, is_required in mandatory_fields.items():
            if is_required:
                field_value = st.session_state[form_state_key].get(field)
                if field_value is None or (isinstance(field_value, str) and field_value.strip() == ""):
                    form_is_valid = False
                    validation_messages.append(f"{field.replace('_', ' ').title()} is required")
        
        if form_is_valid:
            # Submit the form data
            st.success("Form submitted successfully!")
            # Add a user message showing submission
            st.session_state.history.append(Message(
                "human", 
                f"Form submitted with updated data."
            ))
            
            # Process response
            response = process_state(human_prompt="form_submitted", data={"form_data": st.session_state[form_state_key]})
            handle_bot_response(response)
        else:
            # Show validation errors
            for msg in validation_messages:
                st.error(msg)
    
    return st.session_state[form_state_key]

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

            form_data = None
            mandatory_fields = None
            editable_fields = None
            filter_data = None
            filter_config = None
            enable_form = msg.get('enable_form', False)
            
            if enable_form and 'data' in msg and msg['data'] is not None:
                form_data = msg['data'].get('form_data')
                mandatory_fields = msg['data'].get('mandatory_fields')
                editable_fields = msg['data'].get('editable_fields')
                filter_data = msg['data'].get('filter_data')
                filter_config = msg['data'].get('filter_config')

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

            # Add form data as custom attributes to the Message object
            if enable_form and form_data:
                bot_message.enable_form = True
                bot_message.form_data = form_data
                bot_message.mandatory_fields = mandatory_fields
                bot_message.editable_fields = editable_fields
                bot_message.filter_data = filter_data
                bot_message.filter_config = filter_config
            else:
                bot_message.enable_form = False

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


                if hasattr(chat, 'enable_form') and chat.enable_form and i > st.session_state.last_interaction_index:
                    with st.container():
                        st.markdown("""
                        <style>
                        .form-container {
                            border: 1px solid #ccc;
                            border-radius: 10px;
                            padding: 20px;
                            margin: 10px 0;
                            background-color: #f9f9f9;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("View/Edit Form", expanded=True):
                            display_form(
                                chat.form_data, 
                                chat.mandatory_fields, 
                                chat.editable_fields, 
                                chat.filter_data, 
                                chat.filter_config,
                                i
                            )


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