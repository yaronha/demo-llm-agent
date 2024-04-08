from typing import List, Union

from fastapi import APIRouter, Depends, File, Header, Request, UploadFile
from pydantic import BaseModel

from .actions import transcribe_file
from .schema import QueryItem

# Create a router with a prefix
base_router = APIRouter(prefix="/api")


class AuthInfo(BaseModel):
    username: str
    token: str
    roles: List[str] = []


async def startup_event():
    print("\nstartup event\n")


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


@base_router.post("/pipeline/{name}/run")
async def query(
    request: Request, name: str, item: QueryItem, auth=Depends(get_auth_user)
):
    """This is the query command"""
    agent = request.app.extra.get("agent")
    event = {
        "username": auth.username,
        "session_id": item.session_id,
        "query": item.question,
        "collection_name": item.collection,
    }
    resp = agent.run_pipeline(name, event)
    print(f"resp: {resp}")
    return resp


@base_router.get("/tst")
async def tst(request: Request, auth=Depends(get_auth_user)):
    return {"user": auth.username, "extra": request.app.extra}


@base_router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    file_contents = await file.read()
    file_handler = file.file
    return transcribe_file(file_handler)
