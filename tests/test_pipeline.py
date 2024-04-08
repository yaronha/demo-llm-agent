from app.schema import PipelineEvent
from app.client import Client
from app.config import config
from src.controller.sqldb import get_db_session
from src.pipeline import initialize_pipeline
from app.utils import sources_to_text


# test the AppPipeline class, and the initialize_pipeline function
def test_pipeline():
    pipeline = initialize_pipeline(config)
    session = get_db_session()
    result = pipeline.run(
        PipelineEvent(username=None, session_id="234", query="what is a vector?")
    )
    session.close()
    print("Answer:", result["answer"])
    print(sources_to_text(result["sources"]))


def test_list_col():
    client = Client("http://localhost:8000")
    c = client.list_collections(names_only=True)
    print(c)
