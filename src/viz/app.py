import os
import uuid
from typing import Literal

import dash_cytoscape as cyto
import pandas as pd
import vizro.models as vm
from dash import html
from vizro import Vizro
from vizro.models._components.form._user_input import UserInput
from vizro.models.types import capture
from vizro.tables import dash_data_table

from src.client import Client
from src.viz.actions import submit, update
from src.viz.components import ChatbotWindow, CustomUserInput

##
# Set this to True while developing. This will enable hot reloading so that
# the app refreshes whenever you edit the source code and show tracebacks in the browser rather than
# in the console
DEBUG = False
client = Client(os.environ.get("AGENT_API_URL", "http://localhost:8000"))
session_id = uuid.uuid4().hex


def get_collections():
    """get the available indices from the back end"""
    return client.list_collections(names_only=True)


@capture("action")
def submit_ingest(n_clicks: int, data_path: str, collection: str):
    """What happens when you click the Submit button."""
    # Prevent trigger on page load
    if not n_clicks:
        return
    client.ingest(collection, path=data_path, loader="web")
    # requests.post(...)
    print(data_path, collection)


# Used on chatbot screen
def get_llm_response(user_input: str) -> str:
    """What happens when you send a message to the chatbot."""
    # requests.post(...)
    bot_message, sources, state = client.query(
        user_input, collection="default", session_id=session_id
    )
    if sources:
        bot_message += "\n" + sources
    return bot_message


@capture("action")
def new_collection(n_clicks: int, name, description, category="vector"):
    if not n_clicks:
        return
    client.create_collection(name, description=description, db_category=category)


def get_flowchart_elements():
    """Nodes and edges for the flowchart."""
    nodes = [
        {"id": "0", "label": "SessionLoader"},
        {"id": "1", "label": "RefineQuery"},
        {"id": "2", "label": "MultiRetriever"},
        {"id": "3", "label": "HistorySaver"},
    ]
    edges = [
        {"source": "0", "target": "1"},
        {"source": "1", "target": "2"},
        {"source": "2", "target": "3"},
    ]

    return nodes + edges


class Flowchart(vm.VizroBaseModel):
    type: Literal["flowchart"] = "flowchart"

    def build(self):
        return html.Div(
            [
                cyto.Cytoscape(
                    layout={
                        "name": "breadthfirst",
                        "directed": True,
                        "spacingFactor": 1,
                    },
                    style={"width": "100%", "height": "400px"},
                    stylesheet=[
                        {
                            "selector": "node",
                            "style": {
                                "content": "data(label)",
                                "shape": "rectangle",
                                "background-color": "rgba(255, 255, 255, 0.88)",
                                "padding": "4px 8px",
                                "width": "100%",
                                "height": "20px",
                                "color": "rgba(20, 23, 33, 0.88)",
                                "font-size": "12px",
                                "text-wrap": "wrap",
                                "text-halign": "center",
                                "text-valign": "center",
                                "border-color": "#D3D7E0",
                                "border-width": 1,
                            },
                        },
                        {
                            "selector": "edge",
                            "style": {
                                "width": 1,
                                "line-color": "#D3D7E0",
                                "target-arrow-color": "#D3D7E0",
                                "target-arrow-shape": "triangle",
                                "curve-style": "bezier",
                            },
                        },
                    ],
                    elements=[
                        {"data": element} for element in get_flowchart_elements()
                    ],
                )
            ]
        )


# Force style to remain as grid to override grid-layout selector
class GridLayout(vm.Layout):
    def build(self):
        layout = super().build()
        layout.style = {**layout.style, "display": "grid"}
        return layout


# Add custom components
vm.Page.add_type("components", ChatbotWindow)
vm.Page.add_type("components", CustomUserInput)
vm.Page.add_type("components", Flowchart)


# Enable form components to appear in vm.Container and vm.Page.
# UserInput is not in vm namespace since it's not yet public, but it works fine.
vm.Container.add_type("components", vm.Checklist)
vm.Container.add_type("components", vm.Dropdown)
vm.Container.add_type("components", vm.RadioItems)
vm.Container.add_type("components", vm.RangeSlider)
vm.Container.add_type("components", vm.Slider)
vm.Container.add_type("components", UserInput)

vm.Page.add_type("components", vm.Checklist)
vm.Page.add_type("components", vm.Dropdown)
vm.Page.add_type("components", vm.RadioItems)
vm.Page.add_type("components", vm.RangeSlider)
vm.Page.add_type("components", vm.Slider)
vm.Page.add_type("components", UserInput)


@capture("action")
def run_chatbot(store_conversation):  # need store_conversation as input
    """Chatbot interaction."""
    # Get the user input
    user_input_value = store_conversation[-1][1]
    store_conversation.append(("AI", get_llm_response(user_input_value)))
    return store_conversation


pages = []

pages.append(
    vm.Page(
        title="Ingest data",
        components=[
            UserInput(
                id="data_path",
                title="Data path",
                placeholder="http://www.example.com/data",
            ),
            vm.Dropdown(
                id="collection",
                title="Select collection",
                options=get_collections(),
                multi=False,
            ),
            vm.Button(
                id="submit_ingest",
                text="Submit",
                actions=[
                    vm.Action(
                        function=submit_ingest(),
                        inputs=[
                            "submit_ingest.n_clicks",
                            "data_path.value",
                            "collection.value",
                        ],
                    )
                ],
            ),
        ],
    )
)

pages.append(
    vm.Page(
        title="Chatbot",
        layout=GridLayout(grid=[[0], [0], [1]], row_gap="8px", id="chatbot-layout"),
        components=[
            ChatbotWindow(id="chatbot"),
            CustomUserInput(
                id="user_input_id",
                title="User input",
                placeholder="Send a message and press enter...",
                actions=[
                    submit,
                    vm.Action(
                        function=run_chatbot(),  # inputs and outputs need to match above defined action
                        inputs=["store_conversation.data"],
                        outputs=["store_conversation.data"],
                    ),
                    update,
                ],
            ),
        ],
    )
)

data = client.list_collections(names_only=False)
df = pd.DataFrame(data)
pages.append(
    vm.Page(
        title="Data",
        # layout=GridLayout(grid=[[0, 1, 2], [3, 3, 3], [3, 3, 3]], row_gap="8px", id="data-layout"),
        components=[
            vm.Container(
                title="Create New Collection",
                layout=GridLayout(
                    grid=[[0, 1, 2], [3, 3, 3]], row_gap="8px", id="data-layout"
                ),
                components=[
                    UserInput(
                        id="collection_name",
                        title="Collection name",
                        placeholder="default",
                    ),
                    UserInput(id="collection_desc", title="Description"),
                    UserInput(id="collection_type", title="Type", placeholder="vector"),
                    vm.Button(
                        id="add_collection",
                        text="create",
                        actions=[
                            vm.Action(
                                function=new_collection(),
                                inputs=[
                                    "submit_ingest.n_clicks",
                                    "collection_name.value",
                                    "collection_desc.value",
                                    "collection_type.value",
                                ],
                            )
                        ],
                    ),
                ],
            ),
            vm.Table(title="Data Collections", figure=dash_data_table(data_frame=df)),
        ],
    )
)

sdata = client.list_sessions(short=True)
print(sdata)
sdf = pd.DataFrame(sdata)
pages.append(
    vm.Page(
        title="Sessions",
        components=[
            UserInput(id="tst", title="ss", placeholder="default"),
            # vm.Table(title="Chat sessions", figure=dash_data_table(data_frame=sdf)),
        ],
    )
)

pages.append(
    vm.Page(
        title="Pipeline",
        components=[Flowchart()],
    )
)


if __name__ == "__main__":
    dashboard = vm.Dashboard(title="LMM Demo App", pages=pages)
    app = Vizro().build(dashboard).run(debug=DEBUG)
