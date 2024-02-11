from typing import List, Optional, Tuple, Union

from fastapi import Depends, FastAPI, File, Header, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api import chat, collections, users
from src.chains.retrieval import get_retriever_from_config
from src.config import config
from src.schema import IngestItem

app = FastAPI()

# Create a local session factory
engine = create_engine(config.sql_connection_str, echo=config.verbose)
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db_session = None
    try:
        db_session = LocalSession()
        yield db_session
    finally:
        if db_session:
            db_session.close()


class AuthInfo(BaseModel):
    username: str
    token: str
    roles: List[str] = []


# placeholder for extracting the Auth info from the request
async def get_auth_user(
    request: Request, x_username: Union[str, None] = Header(None)
) -> AuthInfo:
    """Get the user from the database"""
    token = request.cookies.get("Authorization", "")
    if x_username:
        return AuthInfo(username=x_username, token=token)
    else:
        return AuthInfo(username="yhaviv@gmail.com", token=token)


@app.post("/query")
async def query(
    item: chat.QueryItem, session=Depends(get_db), auth=Depends(get_auth_user)
):
    """This is the query command"""
    return chat.query(session, item, username=auth.username)


@app.get("/collections")
async def list_collections(
    owner: str = None,
    metadata: Optional[List[Tuple[str, str]]] = None,
    names_only: bool = True,
    session=Depends(get_db),
):
    return collections.list_collections(
        session, owner=owner, metadata=metadata, names_only=names_only
    )


@app.get("/collection/{name}")
async def get_collection(name: str, short: bool = False, session=Depends(get_db)):
    return collections.get_collection(session, name, short=short)


@app.post("/collection/{name}")
async def create_collection(
    request: Request,
    name: str,
    session=Depends(get_db),
    auth: AuthInfo = Depends(get_auth_user),
):
    data = await request.json()
    return collections.create_collection(
        session, name, owner_name=auth.username, **data
    )


@app.post("/collection/{name}/ingest")
async def ingest(name, item: IngestItem, session=Depends(get_db)):
    return collections.ingest(session, name, item)


@app.get("/users")
async def list_users(
    email: str = None,
    username: str = None,
    names_only: bool = True,
    short: bool = False,
    session=Depends(get_db),
):
    return users.get_users(
        session, email=email, username=username, names_only=names_only, short=short
    )


@app.get("/user/{username}")
async def get_user(username: str, session=Depends(get_db)):
    return users.get_user(session, username)


@app.post("/user/{username}")
async def create_user(
    request: Request,
    username: str,
    session=Depends(get_db),
):
    """This is the user command"""
    data = await request.json()
    return users.create_user(session, username, **data)


@app.delete("/user/{username}")
async def delete_user(username: str, session=Depends(get_db)):
    return users.delete_user(session, username)


# add routs for chat sessions, list_sessions, get_session
@app.get("/sessions")
async def list_sessions(
    user: str = None,
    last: int = 0,
    created: str = None,
    short: bool = False,
    session=Depends(get_db),
):
    return chat.list_sessions(
        session, user, created_after=created, last=last, short=short
    )


@app.get("/session/{session_id}")
async def get_session(session_id: str, session=Depends(get_db)):
    return chat.get_session(session, session_id)


@app.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...)):
    file_contents = await file.read()
    file_handler = file.file
    return chat.transcribe_file(file_handler)
