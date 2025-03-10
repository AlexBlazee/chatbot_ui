from dataclasses import dataclass
from typing import Literal
import streamlit as st

import streamlit.components.v1 as components

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
g_user_id = "temp"


@dataclass
class Message:
    """Class for keeping track of a chat message."""
    origin: Literal["human", "ai"]
    message: str

def load_css():
    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)


def process_state(human_prompt = None , files = None , data = None ):
    # chat_request = {
    #     "session_id" : st.session_state.session_id,
    #     "user_id"    : st.session_state.user_id,
    #     "sender"     : "user",
    #     "state"      : st.session_state.state,
    # }
    # if not human_prompt: 
    #     chat_request["messages"] = {
    #         "main_text" : human_prompt,
    #         "files"     : files,
    #         "data"      : data,
    #         "timestamp" : str(datetime.now())
    #     }
    
    # response = requests.post(f"{BASE_URL}/process_state", json= chat_request)
    # if response.status_code == 200: 
    #     st.session_state.state = response["state"]
    #     return response.json()
    # else: 
    #     return "Error processing request"
    response = {'session_id' : "TEMP_SESSION" , 'user_id' : 'temp' , 'sender' : 'bot' , 'state' : 'INITIAL_RESP' , 
                'messages' : [{'main_text' : 'Hello How can I assit you' , 'buttons': ['check the status' , 'submit a concern'] , 
                               'text_area': None , 'text_field': None , 'data' : None , 'time_stamp': datetime.now() , 'enable_text': False, 
                               'enable_text_area': False}]}
    return response



def start_chat(user_id):
    # response = requests.post(f"{BASE_URL}/start_chat", params= {"user_id": user_id})
    # if response.status_code == 200:
    #     response = response.json()
    #     st.session_state.session_id = response["session_id"]
    #     st.session_state.state = response["state"]
    #     st.success("Chat started successfully!")
    # else:
    #     st.error("Failed to start chat.")
    st.session_state.session_id = "TEMP_SESSION"
    st.session_state.state = "INITIAL"

def initialize_session_state():
    if "session_id" not in st.session_state:
        start_chat(g_user_id)
    if "history" not in st.session_state:
        st.session_state.history = []
    # if "token_count" not in st.session_state:
    #     st.session_state.token_count = 0
    # if "conversation" not in st.session_state:
        # llm = OpenAI(
        #     temperature=0,
        #     openai_api_key=st.secrets["openai_api_key"],
        #     model_name="text-davinci-003"
        # )
        # st.session_state.conversation = ConversationChain(
        #     llm=llm,
        #     memory=ConversationSummaryMemory(llm=llm),
        # )
        

def display_bot_response(response):
    messages = response.get("messages", [])
    for message in messages:
        # Display bot's main text message
        if message.get("main_text"):
            div = f"""
<div class="chat-row">
    <img class="chat-icon" src="app/static/ai_icon.png" width=32 height=32>
    <div class="chat-bubble ai-bubble">
        &#8203;{message["main_text"]}
    </div>
</div>
            """
            st.markdown(div, unsafe_allow_html=True)

        # Display buttons if present
        if message.get("buttons"):
            cols = st.columns(len(message["buttons"]))
            for i, button in enumerate(message["buttons"]):
                cols[i].button(button)

        # Display text area if enabled
        if message.get("enable_text_area"):
            st.text_area("Provide more details:", key="text_area_input", placeholder="Type your detailed response here...")

        # Enable or disable text input based on response
        if message.get("enable_text"):
            prompt_placeholder.text_input(
                "Chat",
                label_visibility="collapsed",
                key="human_prompt",
                disabled=False
            )
        else:
            prompt_placeholder.text_input(
                "Chat",
                label_visibility="collapsed",
                key="human_prompt",
                disabled=True
            )

def on_click_callback():
    human_prompt = st.session_state.human_prompt
    # llm_response = st.session_state.conversation.run(
    #     human_prompt
    # )
    bot_response = process_state(human_prompt=human_prompt)

    st.session_state.history.append(
        Message("human", human_prompt)
    )
    bot_message = bot_response["messages"][0].get("main_text" , "")
    st.session_state.history.append(
        Message("ai", bot_message)
    )
    print(bot_response)
    st.session_state.response = bot_response

load_css()
initialize_session_state()

st.title("Hello Custom CSS Chatbot 🤖")

chat_placeholder = st.container()
prompt_placeholder = st.form("chat-form")

with chat_placeholder:
    for chat in st.session_state.history:
        div = f"""
<div class="chat-row 
    {'' if chat.origin == 'ai' else 'row-reverse'}">
    <img class="chat-icon" src="app/static/{
        'ai_icon.png' if chat.origin == 'ai' 
                      else 'user_icon.png'}"
         width=32 height=32>
    <div class="chat-bubble
    {'ai-bubble' if chat.origin == 'ai' else 'human-bubble'}">
        &#8203;{chat.message}
    </div>
</div>
        """
        st.markdown(div, unsafe_allow_html=True)

    for _ in range(3):
        st.markdown("")

display_bot_response(st.session_state.response)


with prompt_placeholder:
    # st.markdown("**Chat**")
    cols = st.columns((6, 1))
    cols[0].text_input(
        "Chat",
        value="Hello bot",
        label_visibility="collapsed",
        key="human_prompt",
    )
    cols[1].form_submit_button(
        "Submit", 
        type="primary", 
        on_click=on_click_callback, 
    )

# credit_card_placeholder.caption(f"""
# Used {st.session_state.token_count} tokens \n
# Debug Langchain conversation: 
# {st.session_state.conversation.memory.buffer}
# """)

components.html("""
<script>
const streamlitDoc = window.parent.document;

const buttons = Array.from(
    streamlitDoc.querySelectorAll('.stButton > button')
);
const submitButton = buttons.find(
    el => el.innerText === 'Submit'
);

streamlitDoc.addEventListener('keydown', function(e) {
    switch (e.key) {
        case 'Enter':
            submitButton.click();
            break;
    }
});
</script>
""", 
    height=0,
    width=0,
)