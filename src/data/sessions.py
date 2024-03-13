from src.api.model import ChatSession
from src.api.sqlclient import client
from src.schema import PipelineEvent


class SessionStore:
    def __init__(self, config=None):
        self.db_session = None

    def get_db_session(self):
        if self.db_session is None:
            self.db_session = client.get_db_session()
        return self.db_session

    def read_state(self, event: PipelineEvent, db_session=None):
        close_session = True if db_session is None else False
        db_session = db_session or self.get_db_session()
        event.username = event.username or "guest"
        event.user = client.get_user(db_session, event.username)
        if event.session_id:
            chat_session = client.get_session(db_session, event.session_id).data
            if chat_session:
                event.session = chat_session
                event.state = chat_session.state
                event.conversation = chat_session.to_conversation()
            else:
                client.create_session(
                    db_session,
                    ChatSession(
                        name=event.session_id, username=event.username or "guest"
                    ),
                )

        if close_session:
            db_session.close()

    def save(self, event: PipelineEvent, db_session=None):
        """Save the session and conversation to the database"""
        if event.session_id:
            close_session = True if db_session is None else False
            db_session = db_session or self.get_db_session()
            client.update_session(
                db_session,
                ChatSession(
                    name=event.session_id,
                    state=event.state,
                    history=event.conversation.to_list(),
                ),
            )

            if close_session:
                db_session.close()


def get_session_store(config):
    # todo: support different session stores
    return SessionStore(config)
