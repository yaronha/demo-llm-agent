from src.data.sqldb import ChatSessions, Users, get_db_session
from src.schema import PipelineEvent


class SessionStore:
    def __init__(self, config=None):
        self.db_session = None

    def get_db_session(self):
        if self.db_session is None:
            self.db_session = get_db_session()
        return self.db_session

    def read_state(self, event: PipelineEvent, db_session=None):
        close_session = True if db_session is None else False
        db_session = db_session or self.get_db_session()
        event.username = event.username or "guest"
        event.user = Users.get(db_session, event.username)
        if event.session_id:
            chat_session = ChatSessions.get(db_session, event.session_id)
            if chat_session:
                event.session = chat_session
                event.state = chat_session.state
                event.conversation = chat_session.to_conversation()
            else:
                ChatSessions.create(
                    db_session, event.session_id, event.username or "guest"
                )

        if close_session:
            db_session.close()

    def save(self, event: PipelineEvent, db_session=None):
        """Save the session and conversation to the database"""
        if event.session_id:
            close_session = True if db_session is None else False
            db_session = db_session or self.get_db_session()
            ChatSessions.update(
                db_session,
                event.session_id,
                state=event.state,
                history=event.conversation.to_list(),
            )

            if close_session:
                db_session.close()


def get_session_store(config):
    # todo: support different session stores
    return SessionStore(config)
