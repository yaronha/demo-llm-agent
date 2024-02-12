"""Actions for the chatbot demo app."""

from typing import List, Tuple

import dash.exceptions
import dash_bootstrap_components as dbc
import vizro.models as vm
from dash import dcc, html
from vizro.models.types import capture


def _create_html_span(icon_name: str, id: str) -> html.Span:
    """Creates a html.Span with the specified icon."""
    return html.Span(icon_name, className="material-symbols-outlined", id=id)


def _update_chatbot_window(message: List[str]) -> html.Div:
    """Renders textbox component."""
    text = message[1]

    if message[0] == "Human":
        thumbnail_human = _create_html_span("person", "thumbnail-human")
        textbox_human = dbc.Card(
            text, body=True, inverse=True, class_name="textbox-human"
        )
        return html.Div([thumbnail_human, textbox_human])
    elif message[0] == "AI":
        thumbnail = _create_html_span("robot_2", "thumbnail-ai")
        textbox = dbc.Card(
            dcc.Markdown(text, link_target="_blank", className="card_text"),
            body=True,
            inverse=False,
            class_name="textbox-ai",
        )
        return html.Div([thumbnail, textbox])
    else:
        raise ValueError("Incorrect option for `box`.")


# TODO: find a way to avoid double action creation if we wanted to use the button
@capture("action")
def submit_message_store(
    user_input_value: str, store_conversation: List[List[str]]
) -> Tuple[List[List[str]], List[html.Div], str]:
    """Add message to store, and update the chat and input windows."""
    if not user_input_value:
        raise dash.exceptions.PreventUpdate

    store_conversation.append(["Human", user_input_value])

    chat_messages = [_update_chatbot_window(message) for message in store_conversation]

    thumbnail = _create_html_span("robot_2", "thumbnail-ai")
    textbox = dbc.Card("Thinking...", body=True, inverse=False, class_name="textbox-ai")
    loader = html.Div([thumbnail, textbox])
    chat_messages.append(loader)

    return store_conversation, chat_messages, ""


@capture("action")
def update_chatbot_window_from_store(store_conversation: List[List[str]]):
    """Update the chatbot window with the conversation result."""
    chat_messages = [_update_chatbot_window(message) for message in store_conversation]
    return chat_messages


submit = vm.Action(
    function=submit_message_store(),
    inputs=["user_input_id.value", "store_conversation.data"],
    outputs=["store_conversation.data", "chatbot.children", "user_input_id.value"],
)

update = vm.Action(
    function=update_chatbot_window_from_store(),
    inputs=["store_conversation.data"],
    outputs=["chatbot.children"],
)
