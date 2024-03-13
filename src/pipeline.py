from src.chains.base import HistorySaver, SessionLoader
from src.chains.pipelines import get_or_create_pipeline
from src.chains.refine import RefineQuery
from src.chains.retrieval import MultiRetriever
from src.config import AppConfig, logger

pipe_config = [
    SessionLoader(),
    RefineQuery(),
    MultiRetriever(),
    HistorySaver(),
]

pipelines = {
    "default": pipe_config,
}


def initialize_pipeline(config: AppConfig, name="default"):
    """Initialize the pipeline"""
    if name not in pipelines:
        raise ValueError(f"Pipeline {name} not found")
    return get_or_create_pipeline(name, pipelines[name], config)
