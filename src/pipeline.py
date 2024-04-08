from src.app.chains.base import HistorySaver, SessionLoader
from src.app.chains.refine import RefineQuery
from src.app.chains.retrieval import MultiRetriever
from src.app.pipelines import app_server

pipe_config = [
    SessionLoader(),
    RefineQuery(),
    MultiRetriever(),
    HistorySaver(),
]

pipelines = {
    "default": pipe_config,
}


app_server.add_pipelines(pipelines)
app = app_server.to_fastapi(with_controller=True)
