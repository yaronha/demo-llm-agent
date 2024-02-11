import datetime

import sqlalchemy
from sqlalchemy import JSON, Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from src.config import config
from src.schema import Conversation

engine = create_engine(config.sql_connection_str, echo=config.verbose)

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()


def create_tables(names: list = None):
    tables = None
    if names:
        tables = [Base.metadata.tables[name] for name in names]
    Base.metadata.create_all(engine, tables=tables, checkfirst=True)


def drop_tables(names: list = None):
    tables = None
    if names:
        tables = [Base.metadata.tables[name] for name in names]
    Base.metadata.drop_all(engine, tables=tables)


def get_db_session():
    return Session()


class User(Base):
    __tablename__ = "users"
    _details_fields = ["features"]

    username = Column(String(255), primary_key=True, nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    created_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_update = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    features = Column(JSON, nullable=True)
    policy = Column(JSON, nullable=True)

    def __init__(self, username, email, full_name, features=None, policy=None):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.features = features
        self.policy = policy

    def __repr__(self):
        return (
            "<User(username='%s', email='%s', fullname='%s', last_update='%s', created_time='%s')>"
            % (
                self.username,
                self.email,
                self.full_name,
                self.last_update,
                self.created_time,
            )
        )

    def to_dict(self, short=False):
        result = {
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "features": self.features,
            "created_time": self.created_time,
            "last_update": self.last_update,
            "policy": self.policy,
        }
        return _format_dict_results(self, result, short)


# create a class for users table crud, similar to the ChatSession class
class Users:
    """Users table CRUD"""

    @staticmethod
    def create(
        session: sqlalchemy.orm.Session,
        username,
        email,
        full_name,
        features=None,
        policy=None,
    ):
        user = User(username, email, full_name, features, policy)
        session.add(user)
        session.commit()

    @staticmethod
    def get(session: sqlalchemy.orm.Session, username):
        try:
            user = session.query(User).filter(User.username == username).first()
        except sqlalchemy.orm.exc.NoResultFound:
            return None
        return user

    @staticmethod
    def update(
        session: sqlalchemy.orm.Session,
        username,
        email=None,
        full_name=None,
        features=None,
        policy=None,
    ):
        session.query(User).filter(User.username == username).update(
            {
                key: value
                for key, value in {
                    "email": email,
                    "full_name": full_name,
                    "features": features,
                    "policy": policy,
                }.items()
                if value is not None
            }
        )
        session.commit()

    @staticmethod
    def delete(session: sqlalchemy.orm.Session, username):
        session.query(User).filter(User.username == username).delete()
        session.commit()

    @staticmethod
    def list(
        session: sqlalchemy.orm.Session, email=None, full_name=None, names_only=False
    ):
        query = session.query(User)
        if email:
            query = query.filter(User.email == email)
        if full_name:
            query = query.filter(User.full_name.like(f"%{full_name}%"))
        users = query.all()
        if names_only:
            return [user.username for user in users]
        return users


class ChatSessionContext(Base):
    """Chat session context table CRUD"""

    __tablename__ = "session_context"
    _details_fields = ["history", "annotations", "features"]

    session_id = Column(String(255), primary_key=True, nullable=False)
    username = Column(
        String(255), sqlalchemy.ForeignKey("users.username"), nullable=False
    )
    agent_name = Column(
        String(255), nullable=True
    )  # for co-pilot, id for the conversation client
    created_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_update = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    history = Column(JSON, nullable=True)  # chat history
    topic = Column(String(255), nullable=True)  # topic of the conversation
    state = Column(JSON, nullable=True)  # session state variables
    annotations = Column(JSON, nullable=True)  # tags, source, links, etc.
    features = Column(JSON, nullable=True)  # features extracted from the chat history

    # Define the relationship with the 'Users' table
    user = relationship(User)

    def __init__(
        self,
        session_id,
        username,
        agent_name=None,
        history=None,
        topic=None,
        state=None,
        annotations=None,
        features=None,
    ):
        self.session_id = session_id
        self.username = username
        self.agent_name = agent_name
        self.history = history
        self.topic = topic
        self.state = state
        self.annotations = annotations
        self.features = features

    def __repr__(self):
        return (
            f"<SessionContext(session_id='{self.session_id}', username='{self.username}', topic='{self.topic}'"
            f", last_update='{self.last_update}', created_time='{self.created_time}', state=`{self.state}`)"
            f", agent_name='{self.agent_name}>"
        )

    def to_dict(self, short=False):
        result = {
            "session_id": self.session_id,
            "username": self.username,
            "agent_name": self.agent_name,
            "history": self.history,
            "topic": self.topic,
            "state": self.state,
            "annotations": self.annotations,
            "features": self.features,
            "created_time": self.created_time,
            "last_update": self.last_update,
        }
        return _format_dict_results(self, result, short)

    def to_conversation(self):
        return Conversation.from_list(self.history)


class ChatSessions:
    @staticmethod
    def create(
        session: sqlalchemy.orm.Session,
        session_id,
        username,
        agent_name=None,
        history=None,
        topic=None,
        state=None,
        annotations=None,
        features=None,
    ):
        if history and isinstance(history, Conversation):
            history = history.to_list()
        session_context = ChatSessionContext(
            session_id,
            username,
            agent_name,
            history,
            topic,
            state,
            annotations,
            features,
        )
        session.add(session_context)
        session.commit()

    @staticmethod
    def get(session: sqlalchemy.orm.Session, session_id):
        try:
            session_context = (
                session.query(ChatSessionContext)
                .filter(ChatSessionContext.session_id == session_id)
                .first()
            )
        except sqlalchemy.orm.exc.NoResultFound:
            return None
        return session_context

    @staticmethod
    def update(
        session: sqlalchemy.orm.Session,
        session_id,
        history,
        topic=None,
        state=None,
        annotations=None,
        features=None,
    ):
        if history and isinstance(history, Conversation):
            history = history.to_list()
        session.query(ChatSessionContext).filter(
            ChatSessionContext.session_id == session_id
        ).update(
            {
                key: value
                for key, value in {
                    "history": history,
                    "topic": topic,
                    "state": state,
                    "annotations": annotations,
                    "features": features,
                }.items()
                if value is not None
            }
        )
        session.commit()

    @staticmethod
    def delete(session: sqlalchemy.orm.Session, session_id):
        session.query(ChatSessionContext).filter(
            ChatSessionContext.session_id == session_id
        ).delete()
        session.commit()

    @staticmethod
    def list(
        session: sqlalchemy.orm.Session, username=None, created_after=None, last=0
    ):
        query = session.query(ChatSessionContext).order_by(
            ChatSessionContext.last_update.desc()
        )
        if username:
            query = query.filter(ChatSessionContext.username == username)
        if created_after:
            if isinstance(created_after, str):
                created_after = datetime.datetime.strptime(
                    created_after, "%Y-%m-%d %H:%M"
                )
            query = query.filter(ChatSessionContext.created_time >= created_after)
        if last > 0:
            query = query.limit(last)
        return query.all()


# Create a class definition for document collections table, with name as a unique key, creation time, last_update, owner, and metadata (key/value dict)
class DocumentCollection(Base):
    __tablename__ = "document_collections"
    _details_fields = ["meta"]

    name = Column(String(255), primary_key=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_update = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    owner_name = Column(
        String(255), sqlalchemy.ForeignKey("users.username"), nullable=True
    )
    meta = Column(JSON, nullable=True)
    db_args = Column(JSON, nullable=True)
    # an enum value for db category (e.g. sql, nosql, document, vector, graph, etc.)
    db_category = Column(String(255), nullable=True)

    owner = relationship(User)

    def __init__(
        self,
        name,
        owner_name,
        description=None,
        meta=None,
        db_args=None,
        db_category=None,
    ):
        self.name = name
        self.description = description
        self.owner_name = owner_name
        self.meta = meta
        self.db_args = db_args
        self.db_category = db_category

    def __repr__(self):
        return (
            f"<DocumentCollection(name='{self.name}', description='{self.description}'"
            f", owner_name='{self.owner_name}', meta='{self.meta}', last_update='{self.last_update}'"
            f", created_time='{self.created_time}'), db_args='{self.db_args}', db_category='{self.db_category}'>"
        )

    def to_dict(self, short=False):
        return _format_dict_results(
            self,
            {
                "name": self.name,
                "description": self.description or "",
                "owner_name": self.owner_name,
                "meta": self.meta,
                "created_time": self.created_time,
                "last_update": self.last_update,
                "db_args": self.db_args,
                "db_category": self.db_category,
            },
            short,
        )


# create a class for document collections table crud, similar to the ChatSession class
class DocumentCollections:
    """Document collections table CRUD"""

    @staticmethod
    def create(
        session: sqlalchemy.orm.Session,
        name,
        description=None,
        owner_name=None,
        meta=None,
        db_args=None,
        db_category=None,
    ):
        document_collection = DocumentCollection(
            name, owner_name, description, meta, db_args, db_category
        )
        session.add(document_collection)
        session.commit()

    @staticmethod
    def get(session: sqlalchemy.orm.Session, name):
        try:
            document_collection = (
                session.query(DocumentCollection)
                .filter(DocumentCollection.name == name)
                .first()
            )
        except sqlalchemy.orm.exc.NoResultFound:
            return None
        return document_collection

    @staticmethod
    def update(
        session: sqlalchemy.orm.Session,
        name,
        description=None,
        meta=None,
        db_args=None,
        db_category=None,
    ):
        session.query(DocumentCollection).filter(
            DocumentCollection.name == name
        ).update(
            {
                key: value
                for key, value in {
                    "description": description,
                    "meta": meta,
                    "db_args": db_args,
                    "db_category": db_category,
                }.items()
                if value is not None
            }
        )
        session.commit()

    @staticmethod
    def delete(session: sqlalchemy.orm.Session, name):
        session.query(DocumentCollection).filter(
            DocumentCollection.name == name
        ).delete()
        session.commit()

    @staticmethod
    def list(
        session: sqlalchemy.orm.Session,
        owner_name=None,
        metadata_match: dict = None,
        names_only=False,
    ):
        query = session.query(DocumentCollection)
        if owner_name:
            query = query.filter(DocumentCollection.owner == owner_name)
        if metadata_match:
            for key, value in metadata_match.items():
                query = query.filter(DocumentCollection.meta[key] == value)
        collections = query.all()
        if names_only:
            return [collection.name for collection in collections]
        return collections

    @staticmethod
    def create_or_update(
        session: sqlalchemy.orm.Session, name, owner_name, description=None, meta=None
    ):
        document_collection = DocumentCollections.get(session, name)
        if document_collection:
            # merge metadata, update values for keys that are in both dicts
            meta = {**document_collection.meta, **(meta or {})}
            DocumentCollections.update(
                session, name, description=description, meta=meta
            )
        else:
            DocumentCollections.create(
                session, name, owner_name, description=description, meta=meta
            )
        return DocumentCollections.get(session, name)


def _format_dict_results(obj, data, short):
    if not short:
        return data

    for key in ["created_time", "last_update"]:
        if key in data:
            data[key] = data[key].strftime("%Y-%m-%d %H:%M")
    return {key: value for key, value in data.items() if key not in obj._details_fields}
