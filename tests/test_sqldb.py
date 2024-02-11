from src.sqldb import (
    ChatSessions,
    DocumentCollections,
    Users,
    create_tables,
    drop_tables,
    get_db_session,
)
from src.api import users


def test_sql_db():
    drop_tables()
    create_tables()

    session = get_db_session()

    Users.create(session, "yh", "Yaron", "x@y.z")
    ChatSessions.create(session, "123", "yh", [{"intent": "test"}])
    # create_chat_session('123', '456', {'intent': 'test'})
    DocumentCollections.create(session, "docs", "yaron", {"type": "web"})

    s = ChatSessions.get(session, "123")
    print("XX:", s, s.user.username)
    ChatSessions.add_to_history(session, "123", {"intent": "test5"})
    ChatSessions.list(session, True)
    # ChatSession.delete(session, "123")

    session.close()


# write a set of unit tests to test the crud operations in the Users class
# (create, get, list, update, delete)


def test_users_crud():
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
def test_chat_sessions_crud():
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


def test_document_collections_crud():
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


def test_prep_db():
    drop_tables()
    create_tables()

    session = get_db_session()

    Users.create(session, "yhaviv@gmail.com", "Yaron Haviv", "yhaviv@gmail.com")
    session.close()


def test_list_collections():
    session = get_db_session()

    doc_collections = DocumentCollections.list(session, names_only=True)
    print(doc_collections)
    session.close()


def test_list_users():
    session = get_db_session()

    us = Users.list(session, names_only=False)
    print(us)

    users_data = users.list_users(session, names_only=False).with_raise()
    print("users_data", users_data)

    session.close()
