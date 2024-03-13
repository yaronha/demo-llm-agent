from typing import List, Optional, Tuple

import openai
import sqlalchemy
from pydantic import BaseModel

from src.api.model import ApiResponse
from src.config import config, logger
from src.doc_loader import get_data_loader, get_loader_obj
from src.pipeline import initialize_pipeline
from src.schema import PipelineEvent


class IngestItem(BaseModel):
    path: str
    loader: str
    metadata: Optional[List[Tuple[str, str]]] = None
    version: Optional[str] = None


def ingest(session: sqlalchemy.orm.Session, collection_name, item: IngestItem):
    """This is the data ingestion command"""
    logger.debug(
        f"Running Data Ingestion: collection_name={collection_name}, path={item.path}, loader={item.loader}"
    )
    data_loader = get_data_loader(
        config, collection_name=collection_name, session=session
    )
    loader_obj = get_loader_obj(item.path, loader_type=item.loader)
    data_loader.load(loader_obj, metadata=item.metadata, version=item.version)
    return ApiResponse(success=True)


class QueryItem(BaseModel):
    question: str
    session_id: Optional[str] = None
    filter: Optional[List[Tuple[str, str]]] = None
    collection: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    returned_state: Optional[dict] = None


def query(session: sqlalchemy.orm.Session, item: QueryItem, username: str = None):
    """This is the query command"""
    logger.debug(f"Running Query for: {item.question} on {item.collection}")
    search_args = {"filter": dict(item.filter)} if item.filter else {}
    returned_state = {}  # TBD for reporting back bot internals

    pipeline = initialize_pipeline(config)
    result = pipeline.run(
        PipelineEvent(
            username=username,
            session_id=item.session_id,
            query=item.question,
            collection_name=item.collection,
        ),
        db_session=session,
    )

    return ApiResponse(
        success=True,
        data=QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            returned_state=returned_state,
        ),
    )


def transcribe_file(file_handler):
    """transcribe audio file using openai API"""
    logger.debug("Transcribing file")
    text = openai.Audio.transcribe("whisper-1", file_handler)
    print(text)
    return ApiResponse(success=True, data=text)
