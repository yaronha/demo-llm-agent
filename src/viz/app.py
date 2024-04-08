import os
import uuid
from typing import Dict, Literal

import dash
import dash_cytoscape as cyto
import pandas as pd
import vizro.models as vm
from dash import ALL, MATCH, Input, Output, State, dcc, html
from vizro import Vizro
from vizro.models._components.form._user_input import UserInput
from vizro.models.types import capture
from vizro.tables import dash_data_table

from src.app.client import Client
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
    return client.list_collections(output_mode="names") or ["default"]


@capture("action")
def submit_ingest(
    n_clicks: int,
    data_path: str,
    collection: str,
    loader: str,
    extra_params: Dict[str, str],
):
    """What happens when you click the Submit button."""
    # Prevent trigger on page load
    if not n_clicks:
        return
    client.ingest(collection, path=data_path, loader=loader)
    print(data_path, collection, extra_params)


# Used on chatbot screen
def get_llm_response(user_input: str, collection) -> str:
    """What happens when you send a message to the chatbot."""
    bot_message, sources, state = client.run_pipeline(
        "", user_input, collection=collection, session_id=session_id
    )
    if sources:
        bot_message += "\n" + sources
    return bot_message


@capture("action")
def new_collection(n_clicks: int, name, description, category):
    if not n_clicks:
        return
    client.create_collection(name, description=description, db_category=category)
    return pd.DataFrame(client.list_collections(output_mode="short")).to_dict("records")


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


class UserInputWithValue(UserInput):
    value: str = None

    def build(self):
        built = super().build()
        if self.value:
            built[self.id].value = self.value
        built.className = "input-container"
        return built


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
vm.Page.add_type("components", UserInputWithValue)


vm.Page.add_type("components", vm.Checklist)
vm.Page.add_type("components", vm.Dropdown)
vm.Page.add_type("components", vm.RadioItems)
vm.Page.add_type("components", vm.RangeSlider)
vm.Page.add_type("components", vm.Slider)
vm.Page.add_type("components", UserInput)
vm.Page.add_type("components", UserInputWithValue)


@capture("action")
def run_chatbot(store_conversation, collection):  # need store_conversation as input
    """Chatbot interaction."""
    # Get the user input
    user_input_value = store_conversation[-1][1]
    store_conversation.append(("AI", get_llm_response(user_input_value, collection)))
    return store_conversation


def make_parameter_div(id, parameter_name, parameter_value, placeholder=True):
    div = html.Div(
        [
            vm.Button.construct(
                id={"type": "delete_parameter", "id": id}, text="Delete"
            ).build(),
            UserInput.construct(
                id={"type": "parameter_name", "id": id}, placeholder=parameter_name
            ).build(),
            UserInput.construct(
                id={"type": "parameter_value", "id": id}, placeholder=parameter_value
            ).build(),
        ],
        className="parameter",
        id={"type": "parameter_container", "id": id},
    )
    if not placeholder:
        div[{"type": "parameter_name", "id": id}].value = parameter_name
        div[{"type": "parameter_value", "id": id}].value = parameter_value
    return div


@dash.callback(
    Output("page-components", "children"),
    inputs={
        "n_clicks": Input("add_parameter", "n_clicks"),
        "page_components": State("page-components", "children"),
    },
)
def add_parameter(n_clicks, page_components):
    # n_clicks = n_clicks or 0  # Since id should be an integer
    if not n_clicks:
        return dash.no_update

    # Use construct to avoid validation rejecting the id as non-string and also to avoid the DuplicateIDError.
    # Insert above the Add parameter button rather than below it as append would do.
    page_components.insert(
        -3, make_parameter_div(n_clicks, "Parameter name", "Parameter value")
    )
    return page_components


@dash.callback(
    output=[
        Output(
            {"type": "parameter_container", "id": MATCH}, "style", allow_duplicate=True
        ),
    ],
    inputs={
        "delete_parameter": Input(
            {"type": "delete_parameter", "id": MATCH}, "n_clicks"
        ),
    },
    prevent_initial_call=True,
)
def delete_parameter(delete_parameter):
    # Note this doesn't actually delete the data from the store.
    if not delete_parameter:
        return dash.no_update

    return [{"display": "none"}]


# Callback for all the keyword parameters
@dash.callback(
    Output("form_data", "data", allow_duplicate=True),
    inputs={
        "parameter_names": Input({"type": "parameter_name", "id": ALL}, "value"),
        "parameter_values": Input({"type": "parameter_value", "id": ALL}, "value"),
        "form_data": State("form_data", "data"),
    },
    prevent_initial_call=True,
)
def update_form_data_for_parameters(parameter_names, parameter_values, form_data):
    for parameter_name, parameter_value in zip(parameter_names, parameter_values):
        # Don't include empty strings
        if parameter_name:
            form_data[parameter_name] = parameter_value
    return form_data


pages = []

pages.append(
    vm.Page(
        title="Chatbot",
        components=[
            ChatbotWindow(id="chatbot"),
            CustomUserInput(
                id="user_input_id",
                placeholder="Send a message and press enter...",
                actions=[
                    submit,
                    vm.Action(
                        function=run_chatbot(),  # inputs and outputs need to match above defined action
                        inputs=["store_conversation.data", "chatbot_collection.value"],
                        outputs=["store_conversation.data"],
                    ),
                    update,
                ],
            ),
            vm.Dropdown(
                id="chatbot_collection",
                title="Select data collection",
                options=get_collections(),
                multi=False,
                value="default",
            ),
        ],
    )
)

pages.append(
    vm.Page(
        title="Ingest data",
        components=[
            UserInputWithValue(
                id="data_path",
                title="Data path",
                value="http://www.example.com/data",
            ),
            vm.Dropdown(
                id="collection",
                title="Select data collection",
                options=get_collections(),
                multi=False,
            ),
            vm.Dropdown(
                id="loader",
                title="Select document loader type",
                options=["web", "eweb", "file"],
                multi=False,
            ),
            vm.Button(id="add_parameter", text="Add parameter"),
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
                            "loader.value",
                            "form_data.data",
                        ],
                    )
                ],
            ),
        ],
    )
)

data = client.list_collections(output_mode="short")
df = pd.DataFrame(data)

pages.append(
    vm.Page(
        title="Data",
        components=[
            vm.Container(
                title="Create New Collection",
                layout=GridLayout(grid=[[0, 1, 2], [3, 3, 3]]),
                components=[
                    UserInput(
                        id="collection_name",
                        title="Collection name",
                    ),
                    UserInput(id="collection_desc", title="Description"),
                    vm.Dropdown(
                        id="collection_type",
                        title="Type",
                        options=["vector"],
                        multi=False,
                    ),
                    vm.Button(
                        id="add_collection",
                        text="Create",
                        actions=[
                            vm.Action(
                                function=new_collection(),
                                inputs=[
                                    "add_collection.n_clicks",
                                    "collection_name.value",
                                    "collection_desc.value",
                                    "collection_type.value",
                                ],
                                outputs=["data_collections.data"],
                            )
                        ],
                    ),
                ],
            ),
            vm.Table(
                title="Data Collections",
                figure=dash_data_table(id="data_collections", data_frame=df),
            ),
        ],
    )
)

sdata = client.list_sessions(output_mode="short") or []
# The state column has difficulty with JSONifying and pandas DataFrame, so remove it
sdf = pd.DataFrame(sdata)
if sdata:
    sdf = sdf.drop(columns=["state"], errors="ignore")

pages.append(
    vm.Page(
        title="Sessions",
        components=[
            vm.Table(
                title="Chat sessions",
                figure=dash_data_table(id="sessions_tbl", data_frame=sdf),
            ),
        ],
        # controls=[vm.Filter(column="username")],
    )
)

pages.append(
    vm.Page(
        title="Pipeline",
        components=[Flowchart()],
    )
)


if __name__ == "__main__":
    dashboard = vm.Dashboard(title="LLM Demo App", pages=pages)
    app = Vizro().build(dashboard)
    app.dash.layout.children.append(dcc.Store(id="form_data", data={}))
    app.run(debug=DEBUG)
