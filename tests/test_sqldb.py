from src.controller.sqlclient import SqlClient
from src.controller.model import User, DocCollection, ChatSession
import yaml



def test_new_users_crud():

    client = SqlClient("sqlite:///:memory:")
    client.create_tables(True)
    session = client.get_db_session()
    resp = client.create_user(User(
        name="yh",
        full_name="Yaron",
        email="x@y.z",
        labels={"type": "web"},
        features={"a": "b"},
    ), session=session)

    print("user:", str(resp.data))
    resp = client.get_user("yh", session=session)
    print(f"get user:\n{yaml.dump(resp.data)}")
    assert resp.data.name == "yh", "expected user name to be yh"
    assert resp.data.labels == {"type": "web"}, "expected labels to be {'type': 'web'}"

    resp = client.update_user(User(name="yh", email="x@y.w", labels={"type": None, "b": "c"}, features={"a": "c", "b": "d"}), session=session)
    print("\nupdated user:", str(resp.data))
    resp = client.get_user("yh", session=session)
    print(f"get user:\n{yaml.dump(resp.data)}")
    assert resp.data.email == "x@y.w", "expected email to be x@y.w"
    assert resp.data.features == {"a": "c", "b": "d"}, "expected features to be {'a': 'c', 'b': 'd'}"

    resp = client.list_users(full_name="Yaron", session=session)
    print(f"\nlist users 1:\n{yaml.dump(resp.data)}")
    assert len(resp.data) == 1, "expected one user"


    resp = client.delete_user("yh", session=session)
    resp = client.list_users(session=session)
    print(f"\nlist users 2:\n{yaml.dump(resp.data)}")
    assert len(resp.data) == 0, "expected no users"
    session.close()


# write a unit tests to test the crud operations of the collections table in the database
# (create, get, list, update, delete), similar to the tests for the Users class in test_new_users_crud
def test_new_collections_crud():
    client = SqlClient("sqlite:///:memory:")
    client.create_tables(True)
    session = client.get_db_session()
    resp = client.create_user(User(
        name="yh",
        full_name="Yaron",
        email="x@y.z",
    ), session=session)
    resp = client.create_collection(DocCollection(
        name="docs",
        owner_name="yh",
        labels={"type": "web"},
        db_args={"a": "b"},
    ), session=session)

    print("collection:", str(resp.data))
    resp = client.get_collection("docs", session=session)
    print(f"get collection:\n{yaml.dump(resp.data)}")
    assert resp.data.name == "docs", "expected collection name to be docs"
    assert resp.data.labels == {"type": "web"}, "expected labels to be {'type': 'web'}"

    resp = client.update_collection(DocCollection(name="docs", category="vector"), session=session)
    print("\nupdated collection:", str(resp.data))
    resp = client.get_collection("docs", session=session)
    print(f"get collection:\n{yaml.dump(resp.data)}")
    assert resp.data.category == "vector", "expected category to be vector"

    resp = client.list_collections(owner="yh", session=session)
    print(f"\nlist collections 1:\n{yaml.dump(resp.data)}")
    assert len(resp.data) == 1, "expected one collection"

    resp = client.delete_collection("docs", session=session)
    resp = client.list_collections(session=session)
    print(f"\nlist collections 2:\n{yaml.dump(resp.data)}")
    assert len(resp.data) == 0, "expected no collections"
    session.close()


# write a unit tests to test the crud operations of the ChatSession table in the database
# (create, get, list, update, delete), similar to the tests for the Users class in test_new_collections_crud
def test_new_sessions_crud():
    client = SqlClient("sqlite:///:memory:")
    client.create_tables(True)
    session = client.get_db_session()
    resp = client.create_user(User(
        name="yh",
        full_name="Yaron",
        email="x@y.z",
    ), session=session)
    resp = client.create_session(ChatSession(
        name="123",
        username="yh",
        history=[{"role": "Human", "content": "what is x?\n"}]
    ), session=session)

    print("session:", str(resp.data))
    resp = client.get_session("123", session=session)
    print(f"get session:\n{yaml.dump(resp.data)}")
    assert resp.data.name == "123", "expected session name to be 123"
    assert resp.data.history[0].role == "Human", "expected role to be Human"

    resp = client.update_session(ChatSession(name="123", features={"a": "b"}), session=session)
    print("\nupdated session:", str(resp.data))
    resp = client.get_session("123", session=session)
    print(f"get session:\n{yaml.dump(resp.data)}")

    resp = client.list_sessions(username="yh", session=session)
    print(f"\nlist sessions 1:\n{yaml.dump(resp.data)}")
    assert len(resp.data) == 1, "expected one session"

    resp = client.delete_session("123", session=session)
    resp = client.list_sessions(session=session)
    print(f"\nlist sessions 2:\n{yaml.dump(resp.data)}")
    assert len(resp.data) == 0, "expected no sessions"
    session.close()


def testt_users_crud():
    drop_tables()
    create_tables()

    session = get_db_session()

    Users.create(session, "yh", "Yaron", "x1@y.z")
    Users.create(session, "yh2", "Yaron2", "x2@y.z")
    Users.create(session, "yh3", "Yaron3", "x3@y.z")
    Users.create(session, "yh4", "Yaron4", "x4@y.z")
    Users.create(session, "yh5", "Yaron5", "x5@y.z")

    user = Users.get(session, "yh")
    assert user.username == "Yaron"
    assert user.email == "x1@y.z"

    users = Users.list(session)
    assert len(users) == 5

    # test update
    Users.update(session, "yh4", "Yaron44", "x44@y.z")
    user = Users.get(session, "yh4")
    assert user.username == "Yaron44"
    assert user.email == "x44@y.z"

    Users.delete(session, "yh")
    users = Users.list(session)
    assert len(users) == 4

    session.close()


# write a set of unit tests to test the crud operations in the ChatSessions class
# (create, get, list, update, delete)
def testt_chat_sessions_crud():
    drop_tables()
    create_tables()

    session = get_db_session()

    Users.create(session, "yh", "Yaron", "x1@y.z")
    Users.create(session, "yh2", "Yaron2", "x2@y.z")
    Users.create(session, "yh3", "Yaron3", "x3@y.z")
    Users.create(session, "yh4", "Yaron4", "x4@y.z")
    Users.create(session, "yh5", "Yaron5", "x5@y.z")

    ChatSessions.create(session, "123", "yh", [{"intent": "test"}])
    ChatSessions.create(session, "1234", "yh2", [{"intent": "test2"}])
    ChatSessions.create(session, "1235", "yh3", [{"intent": "test3"}])
    ChatSessions.create(session, "1236", "yh4", [{"intent": "test4"}])
    ChatSessions.create(session, "1237", "yh5", [{"intent": "test5"}])

    # test get
    chat_session = ChatSessions.get(session, "123")
    assert chat_session.user.username == "Yaron"
    assert chat_session.history[0]["intent"] == "test"

    # test list
    chat_sessions = ChatSessions.list(session)
    assert len(chat_sessions) == 5

    # test update
    ChatSessions.update(session, "123", [{"intent": "test6"}])
    chat_session = ChatSessions.get(session, "123")
    assert chat_session.history[0]["intent"] == "test6"

    # test add_to_history
    ChatSessions.add_to_history(session, "123", {"intent": "test7"})
    chat_session = ChatSessions.get(session, "123")
    assert chat_session.history[1]["intent"] == "test7"

    # test delete
    ChatSessions.delete(session, "123")
    chat_sessions = ChatSessions.list(session)
    assert len(chat_sessions) == 4

    session.close()


def testt_document_collections_crud():
    drop_tables()
    create_tables()

    session = get_db_session()

    Users.create(session, "yh", "Yaron", "x1@y.z")
    Users.create(session, "yh2", "Yaron2", "x2@y.z")
    Users.create(session, "yh3", "Yaron3", "x3@y.z")
    Users.create(session, "yh4", "Yaron4", "x4@y.z")
    Users.create(session, "yh5", "Yaron5", "x5@y.z")

    DocumentCollections.create(session, "docs", "yh", {"type": "web"})
    DocumentCollections.create(session, "docs2", "yh2", {"type": "web2"})
    DocumentCollections.create(session, "docs3", "yh3", {"type": "web3"})
    DocumentCollections.create(session, "docs4", "yh4", {"type": "web4"})
    DocumentCollections.create(session, "docs5", "yh5", {"type": "web5"})

    # test get
    doc_collection = DocumentCollections.get(session, "docs")
    assert doc_collection.name == "docs"
    assert doc_collection.owner.username == "Yaron"
    assert doc_collection.meta["type"] == "web"

    # test list
    doc_collections = DocumentCollections.list(session)
    assert len(doc_collections) == 5

    # test list_names
    doc_collections = DocumentCollections.list_names(session)
    assert len(doc_collections) == 5
    assert doc_collections[0] == "docs"

    # test update
    DocumentCollections.update(session, "docs", {"type": "web6"})
    doc_collection = DocumentCollections.get(session, "docs")
    assert doc_collection.meta["type"] == "web6"

    # test create_or_update
    DocumentCollections.create_or_update(session, "docs", "yh", {"type": "web7"})
    doc_collection = DocumentCollections.get(session, "docs")
    assert doc_collection.meta["type"] == "web7"

    # test delete
    DocumentCollections.delete(session, "docs")
    doc_collections = DocumentCollections.list(session)
    assert len(doc_collections) == 4

    session.close()
