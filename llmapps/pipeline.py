from llmapps.app.chains.base import HistorySaver, SessionLoader
from llmapps.app.chains.refine import RefineQuery
from llmapps.app.chains.retrieval import MultiRetriever
from llmapps.app.pipelines import app_server

pipe_graph = [
    SessionLoader(),
    RefineQuery(),
    MultiRetriever(),
    HistorySaver(),
]


app_server.add_pipeline("default", pipe_graph)
app = app_server.to_fastapi(with_controller=True)
