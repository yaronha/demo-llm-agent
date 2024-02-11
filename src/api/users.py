import sqlalchemy

from src.config import logger
from src.schema import ApiResponse
from src.sqldb import Users


def get_user(session: sqlalchemy.orm.Session, username: str):
    """This is the user command"""
    logger.debug(f"Getting user: username={username}")
    user = Users.get(session, username)
    if user:
        return ApiResponse(success=True, data=[user.to_dict()])
    else:
        return ApiResponse(success=False, error="User not found")


def delete_user(session: sqlalchemy.orm.Session, username: str):
    """This is the delete user command"""
    logger.debug(f"Deleting user: username={username}")
    user = Users.get(session, username)
    if user:
        Users.delete(session, username)
        return ApiResponse(success=True)
    else:
        return ApiResponse(success=False, error="User not found")


def create_user(session: sqlalchemy.orm.Session, username: str, **kwargs):
    """This is the create user command"""
    logger.debug(f"Creating user: username={username}, {kwargs}")
    Users.create(session, username, **kwargs)
    return ApiResponse(success=True)


def list_users(
    session: sqlalchemy.orm.Session,
    email: str = None,
    full_name: str = None,
    names_only: bool = False,
    short: bool = False,
):
    """This is the list users command"""
    logger.debug(
        f"Getting users: full_name~={full_name}, email={email}, names_only={names_only}"
    )
    users = Users.list(session, full_name=full_name, email=email)
    print(users)
    if not names_only:
        users = [user.to_dict(short) for user in users]
    return ApiResponse(success=True, data=users)
