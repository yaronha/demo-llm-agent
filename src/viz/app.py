import logging
import os
import uuid
from typing import Literal, Dict

try:
    from pydantic.v1 import Field, validator
except ImportError:  # pragma: no cov
    from pydantic import Field, validator
import dash
from dash import Patch
import dash_bootstrap_components as dbc
import vizro.models as vm
from dash import dcc
from vizro import Vizro
from vizro.models import Page
from vizro.models._components.form._user_input import UserInput
from vizro.models._page import _PageBuildType
from vizro.models.types import capture

from src.client import Client
from src.viz.actions import _update_chatbot_window
from src.viz.components import ChatbotWindow, TextArea

##
# Set this to True while developing. This will enable hot reloading so that
# the app refreshes whenever you edit the source code and show tracebacks in the browser rather than
# in the console
DEBUG = False
client = Client(os.environ.get("AGENT_API_URL", "http://localhost:8000"))
this_session_id = uuid.uuid4().hex


##########################
# Main API calls
def get_collections():
    """get the available indices from the back end"""
    return client.list_collections(names_only=True)


# Used on chatbot screen
def query_llm(user_input: str, collection) -> str:
    """What happens when you send a message to the chatbot."""
    bot_message, sources, state = client.query(
        user_input, collection=collection, session_id=this_session_id
    )
    if sources:
        bot_message += "\n" + sources
    # No need to return anything since chat is populated from session history
    # This means the sources are ignored
    # return bot_message


def get_recent_chat_histories(n: int = None):
    """Get most recent n chat histories. Searches through all sessions.
    Gives most recent history first."""
    sessions = client.list_sessions()
    histories = []

    for session in sessions:
        # TODO: Should really be a yield until have n entries
        if not session["history"]:
            continue
        histories.append((session["session_id"], format_session_history(session)))

    return histories if n is None else histories[:n]


##########################
# Helper functions
def format_session_history(session):
    if not session or not session["history"]:
        return []
    return [(line["role"], line["content"]) for line in session["history"]]


@capture("action")
def add_thinking_box(user_input_value):
    if not user_input_value:
        raise dash.exceptions.PreventUpdate
    chatbot_children = Patch()
    chatbot_children.append(_update_chatbot_window(["Human", user_input_value]))
    chatbot_children.append(_update_chatbot_window(["AI", "Thinking..."]))

    return chatbot_children, "", user_input_value


@capture("action")
def run_chatbot(stored_user_input_value, collection):
    """Chatbot interaction."""
    query_llm(stored_user_input_value, collection)
    return [
        _update_chatbot_window(message)
        for message in format_session_history(
            client.get_session(session_id=this_session_id)
        )
    ]


# Enable form components to appear in vm.Container and vm.Page.
# UserInput is not in vm namespace since it's not yet public, but it works fine.
vm.Container.add_type("components", vm.Checklist)
vm.Container.add_type("components", vm.Dropdown)
vm.Container.add_type("components", vm.RadioItems)
vm.Container.add_type("components", vm.RangeSlider)
vm.Container.add_type("components", vm.Slider)
vm.Container.add_type("components", UserInput)
vm.Container.add_type("components", TextArea)
vm.Container.add_type("components", ChatbotWindow)

vm.Page.add_type("components", vm.Checklist)
vm.Page.add_type("components", vm.Dropdown)
vm.Page.add_type("components", vm.RadioItems)
vm.Page.add_type("components", vm.RangeSlider)
vm.Page.add_type("components", vm.Slider)
vm.Page.add_type("components", UserInput)
vm.Page.add_type("components", TextArea)
vm.Page.add_type("components", ChatbotWindow)


this_session_chatbot_components = [
    ChatbotWindow(id="chatbot"),
    TextArea(id="user_input_id", placeholder="Write a message and press Submit..."),
    vm.Dropdown(
        id="chatbot_collection",
        title="Select data collection",
        options=get_collections(),
        multi=False,
        value="default",
    ),
    vm.Button(
        text="Submit",
        id="submit",
        actions=[
            vm.Action(
                function=add_thinking_box(),  # inputs and outputs need to match above defined
                inputs=["user_input_id.value"],
                outputs=[
                    "chatbot.children",
                    "user_input_id.value",
                    "store_conversation.data",
                ],
            ),
            vm.Action(
                function=run_chatbot(),  # inputs and outputs need to match above defined action
                inputs=["store_conversation.data", "chatbot_collection.value"],
                outputs=["chatbot.children"],
            ),
        ],
    ),
]


class ChatbotPage(vm.Page):
    def build(self, session_id=this_session_id) -> _PageBuildType:
        self.title = "Current chat" if session_id == this_session_id else session_id[:5]

        if session_id == this_session_id:
            self.components = this_session_chatbot_components
        else:
            self.components = [
                ChatbotWindow(
                    data=format_session_history(
                        client.get_session(session_id=session_id)
                    )
                )
            ]
        self.layout = vm.Layout(grid=[[i] for i in range(len(self.components))])

        built = super().build()
        if session_id == this_session_id:
            # Need to repopulate so when you switch back to current chat page it is still populated
            built["chatbot"].children = [
                _update_chatbot_window(message)
                for message in format_session_history(
                    client.get_session(session_id=session_id)
                )
            ]
        return built


page = ChatbotPage(title="Chatbot", components=[ChatbotWindow()])


class ChatbotDashboard(vm.Dashboard):
    # Needed to pass session_id through as query parameter
    def _make_page_layout(self, page: Page, session_id=this_session_id):
        page_divs = self._get_page_divs(page=page)
        page_content: _PageBuildType = page.build(session_id)
        control_panel = page_content["control-panel"]
        page_components = page_content["page-components"]
        page_divs["control-panel"] = control_panel
        page_divs["page-components"] = page_components
        page_divs["page-title"].children = page.title
        return self._arrange_page_divs(page_divs=page_divs)


class ChatAccordion(vm.Accordion):
    # Removed validation that checks dash page registry
    def _create_accordion_buttons(self, pages, active_page_id):
        """Creates a button for each provided page that is registered."""
        accordion_buttons = []

        for session_id in pages:
            session_name = (
                "Current chat" if session_id == this_session_id else session_id[:5]
            )
            accordion_buttons.append(
                dbc.Button(
                    children=[session_name],
                    className="accordion-item-button",
                    active=False,  # page["session_id"] == active_page_id,
                    href="?session_id=" + session_id,
                )
            )
        return accordion_buttons


ChatAccordion.__fields__["pages"].validators = []
ChatAccordion.__fields__["pages"].post_validators = None

sessions = [this_session_id] + [
    session_id for session_id, session_history in get_recent_chat_histories()
]

if __name__ == "__main__":
    dashboard = ChatbotDashboard(
        title="LLM Demo App",
        pages=[page],
        navigation=vm.Navigation(nav_selector=ChatAccordion(pages=sessions)),
    )
    app = Vizro().build(dashboard)
    app.dash.layout.children.append(dcc.Store(id="form_data", data={}))
    app.run(debug=DEBUG)
