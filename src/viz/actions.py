"""Actions for the chatbot demo app."""

from typing import List, Tuple

import dash.exceptions
import dash_bootstrap_components as dbc
import vizro.models as vm
from dash import dcc, html
from vizro.models.types import capture

from dash import dcc


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
