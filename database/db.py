from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging

Base = declarative_base()
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_url: str):
        self._engine = create_engine(db_url, echo=True)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self):
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self):
        session = self._session_factory()
        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()
