from typing import List, Optional, Tuple

import openai
import sqlalchemy
from pydantic import BaseModel

from src.config import config, logger
from src.pipeline import initialize_pipeline
from src.schema import ApiResponse, PipelineEvent
from src.data.sqldb import ChatSessions
from src.utils import sources_to_md


class QueryItem(BaseModel):
    question: str
    session_id: Optional[str] = None
    filter: Optional[List[Tuple[str, str]]] = None
    collection: Optional[str] = None


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
        data={
            "answer": result["answer"],
            "sources": sources_to_md(result["sources"]),
            "returned_state": returned_state,
        },
    )


def list_sessions(
    session: sqlalchemy.orm.Session,
    username: str = None,
    created_after: str = None,
    last=None,
    short: bool = False,
):
    """This is the list chat sessions command"""
    logger.debug(
        f"Getting chat sessions: username={username}, created_after={created_after}, last={last}"
    )
    sessions = ChatSessions.list(
        session, username=username, created_after=created_after, last=last
    )
    return ApiResponse(success=True, data=[s.to_dict(short) for s in sessions])


def get_session(session: sqlalchemy.orm.Session, session_id: str):
    """This is the chat session command"""
    logger.debug(f"Getting chat session: session_id={session_id}")
    session = ChatSessions.get(session, session_id)
    if session:
        return ApiResponse(success=True, data=session.to_dict())
    else:
        return ApiResponse(success=False, error="Session not found")


def transcribe_file(file_handler):
    """transcribe audio file using openai API"""
    logger.debug(f"Transcribing file")
    text = openai.Audio.transcribe("whisper-1", file_handler)
    print(text)
    return ApiResponse(success=True, data=text)
