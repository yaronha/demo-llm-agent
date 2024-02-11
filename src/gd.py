import os
import uuid

import gradio as gr

from client import Client

client = Client(os.environ.get("AGENT_API_URL", "http://localhost:8000"))


def get_catalog():
    """get the available indices from the back end"""
    return client.list_collections(names_only=True)


def invoke_chat(query: str, session_id: str, username: str, index: str):
    """Invoke the backend chat API"""
    print(f"Got request - session: {session_id}, user: {username}")
    return client.query(query, index, session_id=session_id)


def transcribe_audio(audio_file):
    """Transcribe audio using Google speech to text API"""

    # todo
    return "fake text", None


def get_uuid():
    """Generate unique session id"""
    return uuid.uuid4().hex


with gr.Blocks(analytics_enabled=False, theme=gr.themes.Soft()) as demo:
    session_obj = gr.State(get_uuid)

    with gr.Row():
        with gr.Column(scale=5):
            chatbot = gr.Chatbot([], elem_id="chatbot")  # .style(height=600)
        with gr.Column(scale=1):
            indices = get_catalog()
            username = gr.Dropdown(
                ["Joe", "Mike", "Sophie"], label="User (persona)", value="Joe"
            )
            index = gr.Dropdown(indices, label="Index", value=indices[0])
            # audio = gr.Audio(
            #     sources=["microphone"], type="filepath", label="Voice input"
            # )
            resp_state = gr.JSON({}, label="Bot state")
            clear = gr.Button("Clear")
    with gr.Row():
        msg = gr.Textbox(label="Q:", placeholder="Type a question and Enter")

    def respond(message, chat_history, index, user, session):
        index_key = index.split(":")[0]

        # call the backend
        bot_message, sources, state = invoke_chat(message, session, user, index_key)

        # If there are sources associated with the answer, convert them to markdown
        if sources:
            bot_message += "\n" + sources

        # update the chat history
        chat_history.append((message, bot_message))
        return "", chat_history, state

    msg.submit(
        respond,
        [msg, chatbot, index, username, session_obj],
        [msg, chatbot, resp_state],
    )
    # transcribe the audio (post recording)
    # audio.change(transcribe_audio, audio, [msg, audio])

    clear.click(lambda: None, None, chatbot, queue=False)

demo.launch()
