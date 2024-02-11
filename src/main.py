# main file with cli commands using python click library
# include two click commands: 1. data ingestion (using the data loader), 2. query (using the agent)

import click
import yaml
from tabulate import tabulate

from src.api import chat, collections, users
from src.data.sqldb import (
    DocumentCollections,
    Users,
    create_tables,
    drop_tables,
    get_db_session,
)

from .config import config
from .doc_loader import get_data_loader, get_loader_obj
from .pipeline import initialize_pipeline
from .schema import PipelineEvent
from .utils import sources_to_text


@click.group()
def cli():
    pass


# click command for initializing the database tables
@click.command()
def initdb():
    """Initialize the database (delete old tables)"""
    click.echo(f"Running Init DB")
    drop_tables()
    create_tables()
    session = get_db_session()
    # create a guest user, and the defualt document collection
    Users.create(session, "guest", email="guest@any.com", full_name="Guest User")
    DocumentCollections.create(
        session,
        "default",
        description="Default Collection",
        owner_name="guest",
        db_category="vector",
    )
    session.close()


@click.command("config")
def print_config():
    """Print the config as a yaml file"""
    click.echo(f"Running Config")
    click.echo(yaml.dump(config.dict()))


@click.command()
@click.argument("path", type=str)
@click.option("-l", "--loader", type=str, help="Type of data loader")
@click.option(
    "-m", "--metadata", type=(str, str), multiple=True, help="Metadata Key value pair"
)
@click.option("-v", "--version", type=str, help="document version")
@click.option("-c", "--collection", type=str, help="Vector DB collection name")
@click.option(
    "-f", "--from-file", is_flag=True, help="Take the document paths from the file"
)
def ingest(path, loader, metadata, version, collection, from_file):
    """Ingest documents into the vector database"""
    create_tables()
    data_loader = get_data_loader(config, collection_name=collection)
    if from_file:
        with open(path, "r") as fp:
            lines = fp.readlines()
        for line in lines:
            path = line.strip()
            click.echo(f"Using loader: {loader}")
            if path and not path.startswith("#"):
                click.echo(f"Loading from path: {path}")
                loader_obj = get_loader_obj(path, loader_type=loader)
                data_loader.load(loader_obj, metadata=metadata, version=version)

    else:
        loader_obj = get_loader_obj(path, loader_type=loader)
        data_loader.load(loader_obj, metadata=metadata, version=version)
        click.echo(f"Running Data Ingestion from: {path} with loader: {loader}")


@click.command()
@click.argument("question", type=str)
@click.option(
    "-f",
    "--filter",
    type=(str, str),
    multiple=True,
    help="Search filter Key value pair",
)
@click.option("-c", "--collection", type=str, help="Vector DB collection name")
@click.option("-u", "--user", type=str, help="Username")
@click.option("-v", "--verbose", is_flag=True, help="Verbose mode")
@click.option("-s", "--session", type=str, help="Session ID")
def query(question, filter, collection, user, verbose, session):
    """Run a chat quary on the vector database collection"""
    click.echo(f"Running Query for: {question}")

    search_args = {"filter": dict(filter)} if filter else {}
    pipeline = initialize_pipeline(config, verbose=verbose)
    result = pipeline.run(
        PipelineEvent(
            username=user,
            session_id=session,
            query=question,
            collection_name=collection,
        )
    )
    click.echo(result["answer"])
    click.echo(sources_to_text(result["sources"]))


# create a child click group for listing database tables in sqldb.py (users, document collections), with two commands: 1. list users, 2. list collections
@click.group()
def list():
    """List the different objects in the database (by category)"""
    pass


@click.group()
def update():
    """Create or update an object in the database"""
    pass


@click.command("users")
@click.option("-u", "--user", type=str, help="user name filter")
@click.option("-e", "--email", type=str, help="email filter")
def list_users(user, email):
    """List users"""
    click.echo("Running List Users")

    session = get_db_session()
    data = users.list_users(session, email, user, short=True).with_raise()
    table = format_table_results(data.data)
    click.echo(table)
    session.close()


# add a command to list document collections, similar to the list users command
@click.command("collections")
@click.option("-o", "--owner", type=str, help="owner filter")
@click.option(
    "-m", "--metadata", type=(str, str), multiple=True, help="metadata filter"
)
def list_collections(owner, metadata):
    """List document collections"""
    click.echo("Running List Collections")

    session = get_db_session()
    data = collections.list_collections(
        session, owner, metadata, short=True
    ).with_raise()
    table = format_table_results(data.data)
    click.echo(table)
    session.close()


# add a command for creating or updating a collection, using the collections.create_collection function, and accept all the same arguments as click options
@click.command("collection")
@click.argument("name", type=str)
@click.option("-o", "--owner", type=str, help="owner name")
@click.option("-d", "--description", type=str, help="collection description")
@click.option("-c", "--category", type=str, help="collection category")
@click.option("-m", "--metadata", multiple=True, default=[], help="metadata filter")
def update_collection(name, owner, description, category, metadata):
    """Create or update a document collection"""
    click.echo("Running Create or Update Collection")
    metadata = fill_params(metadata)

    session = get_db_session()
    # check if the collection exists, if it does, update it, otherwise create it
    collection_exists = collections.get_collection(session, name).success
    if collection_exists:
        collections.update_collection(
            session, name, description, db_category=category, meta=metadata
        ).with_raise()
    else:
        collections.create_collection(
            session,
            name,
            description,
            owner_name=owner,
            db_category=category,
            meta=metadata,
        ).with_raise()


# add a commant to list chat sessions, similar to the list_users command
@click.command("sessions")
@click.option("-u", "--user", type=str, help="user name filter")
@click.option("-l", "--last", type=int, default=0, help="last n sessions")
@click.option("-c", "--created", type=str, help="created after date")
def list_sessions(user, last, created):
    """List chat sessions"""
    click.echo("Running List Sessions")

    session = get_db_session()
    data = chat.list_sessions(session, user, created, last, short=True).with_raise()
    table = format_table_results(data.data)
    click.echo(table)
    session.close()


def format_table_results(table_results):
    return tabulate(table_results, headers="keys", tablefmt="fancy_grid")


def fill_params(params, params_dict=None):
    params_dict = params_dict or {}
    for param in params:
        i = param.find("=")
        if i == -1:
            continue
        key, value = param[:i].strip(), param[i + 1 :].strip()
        if key is None:
            raise ValueError(f"cannot find param key in line ({param})")
        params_dict[key] = value
    if not params_dict:
        return None
    return params_dict


cli.add_command(ingest)
cli.add_command(query)
cli.add_command(initdb)
cli.add_command(print_config)

cli.add_command(list)
list.add_command(list_users)
list.add_command(list_collections)
list.add_command(list_sessions)

cli.add_command(update)
update.add_command(update_collection)

if __name__ == "__main__":
    cli()
