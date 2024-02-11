from typing import List, Optional, Tuple

import sqlalchemy

from src.config import config, logger
from src.data.sqldb import DocumentCollections
from src.doc_loader import get_data_loader, get_loader_obj
from src.schema import ApiResponse, IngestItem


def list_collections(
    session: sqlalchemy.orm.Session,
    owner: str = None,
    metadata: Optional[List[Tuple[str, str]]] = None,
    names_only: bool = False,
    short: bool = False,
):
    """This is the list collections command"""
    logger.debug(
        f"Getting collections: owner={owner}, metadata={metadata}, names_only={names_only}"
    )
    collections = DocumentCollections.list(
        session, owner_name=owner, metadata_match=metadata, names_only=names_only
    )
    if not names_only:
        collections = [col.to_dict(short) for col in collections]
    return ApiResponse(success=True, data=collections)


def get_collection(session: sqlalchemy.orm.Session, name: str):
    """This is the collection command"""
    logger.debug(f"Getting collection: name={name}")
    collection = DocumentCollections.get(session, name)
    if collection:
        return ApiResponse(success=True, data=[collection.to_dict()])
    else:
        return ApiResponse(success=False, error="Collection not found")


def delete_collection(session: sqlalchemy.orm.Session, name: str):
    """This is the delete collection command"""
    logger.debug(f"Deleting collection: name={name}")
    collection = DocumentCollections.get(session, name)
    if collection:
        DocumentCollections.delete(session, name)
        return ApiResponse(success=True)
    else:
        return ApiResponse(success=False, error="Collection not found")


def create_collection(
    session: sqlalchemy.orm.Session,
    name: str,
    description: str,
    owner_name: str = None,
    **kwargs,
):
    """This is the create collection command"""
    logger.debug(f"Creating collection: name={name}, {kwargs}")
    DocumentCollections.create(session, name, description, owner_name, **kwargs)
    return ApiResponse(success=True)


def update_collection(
    session: sqlalchemy.orm.Session, name: str, description: str, **kwargs
):
    """This is the create collection command"""
    logger.debug(f"Creating collection: name={name}, {kwargs}")
    DocumentCollections.update(session, name, description, **kwargs)
    return ApiResponse(success=True)


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
