"""User input component."""

from dash import dcc, html
from vizro.models._action._actions_chain import Trigger

try:
    from pydantic.v1 import Field, validator
except ImportError:
    from pydantic import validator, Field

from typing import List, Literal

import dash_bootstrap_components as dbc
from vizro.models import Action, VizroBaseModel
from vizro.models._action._actions_chain import _action_validator_factory
from vizro.models._models_utils import _log_call


class TextArea(VizroBaseModel):
    """Component provided to `Form` to allow user multi-line text input.

    Args:
        type (Literal["text_area"]): Defaults to `"text_area"`.
        title (str): Title to be displayed. Defaults to `""`.
        placeholder (str): Default text to display in input field. Defaults to `""`.
        actions (Optional[List[Action]]): Defaults to `[]`.

    """

    type: Literal["text_area"] = "text_area"
    # TODO: before making public consider naming this field (or giving an alias) label instead of title
    title: str = Field("", description="Title to be displayed")
    placeholder: str = Field("", description="Default text to display in input field")
    value: str = None
    actions: List[Action] = []

    # Re-used validators
    # TODO: Before making public, consider how actions should be triggered and what the default property should be
    # See comment thread: https://github.com/mckinsey/vizro/pull/298#discussion_r1478137654
    _set_actions = _action_validator_factory("value")

    @_log_call
    def build(self):
        return html.Div(
            [
                html.Label(self.title, htmlFor=self.id) if self.title else None,
                dbc.Textarea(
                    id=self.id,
                    placeholder=self.placeholder,
                    persistence=True,
                    persistence_type="session",
                    value=self.value,
                    debounce=True,
                    style={"width": "100%", "height": "100px"},
                ),
            ],
            className="input-container",
            id=f"{self.id}_outer",
        )


class CustomUserInput(TextArea):
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
