"""User input component."""
from vizro.models._action._actions_chain import Trigger
from vizro.models._components.form._user_input import UserInput

from typing import Literal

import dash_bootstrap_components as dbc
from dash import dcc, html

from vizro.models import VizroBaseModel
from vizro.models._models_utils import _log_call

try:
    from pydantic.v1 import validator
except ImportError:
    from pydantic import validator


class CustomUserInput(UserInput):
    """Custom input form."""

    @validator("actions")
    def _validate_actions(cls, v, values):
        v[0].trigger = Trigger(component_id=values["id"], component_property="n_submit")
        return v


class ChatbotWindow(VizroBaseModel):
    """Component to render chatbot.

    Args:
        type (Literal["render_chatbot"]): Defaults to `"render_chatbot"`.
    """

    type: Literal["render_chatbot"] = "render_chatbot"

    @_log_call
    def build(self):
        """Builds chatbot component."""
        return html.Div(
            [
                dcc.Store(id="store_conversation", data=[]),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(
                                    html.Div(id=self.id),
                                    className="display-conversation-container",
                                ),
                            ],
                            className="card_text",
                        )
                    ],
                    className="card_container",
                ),
            ],
            className="outer-container",
        )
