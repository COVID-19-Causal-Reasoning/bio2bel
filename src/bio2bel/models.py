# -*- coding: utf-8 -*-

"""Bio2BEL database models."""

import datetime
import logging

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from bio2bel.constants import get_global_connection

log = logging.getLogger(__name__)

Base = declarative_base()

TABLE_PREFIX = 'bio2bel'
ACTION_TABLE_NAME = '{}_action'.format(TABLE_PREFIX)


def _make_session():
    """Make a session.

    :rtype: sqlalchemy.orm.Session
    """
    connection = get_global_connection()

    engine = create_engine(connection)
    Base.metadata.create_all(engine, checkfirst=True)

    session_cls = sessionmaker(bind=engine)
    return session_cls()


def _store_helper(make_method, resource, session=None):
    """
    :param make_method: Either :meth:`Action.make_populate` or :meth:`Action.make_drop`
    :param str resource: The lowercase name of the resource. Ex: 'interpro'
    :param Optional[sqlalchemy.orm.Session] session: A pre-built session
    :rtype: Action
    """
    if session is None:
        session = _make_session()

    model = make_method(resource)
    session.add(model)
    session.commit()
    session.close()

    return model


class Action(Base):
    """Represents an update, dropping, population, etc. to the database."""

    __tablename__ = ACTION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    resource = Column(String(32), nullable=False,
                      doc='The normalized name of the Bio2BEL package (e.g., hgnc, chebi, etc)')
    action = Column(String(32), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, doc='The date and time of upload')

    @classmethod
    def make_populate(cls, resource):
        """Make a ``populate`` instance of :class:`Action`.

        :rtype: Action
        """
        return Action(resource=resource.lower(), action='populate')

    @classmethod
    def make_drop(cls, resource):
        """Make a ``drop`` instance of :class:`Action`.

        :rtype: Action
        """
        return Action(resource=resource.lower(), action='drop')

    @classmethod
    def store_populate(cls, resource, session=None):
        """Store a populate event.

        :param str resource: The normalized name of the resource to store
        :param Optional[sqlalchemy.orm.Session] session: A pre-built session
        :rtype: Action

        Example:

        >>> from bio2bel.models import Action
        >>> Action.store_populate('hgnc')
        """
        return _store_helper(cls.make_populate, resource, session=session)

    @classmethod
    def store_drop(cls, resource, session=None):
        """Store a drop event.

        :param str resource: The normalized name of the resource to store
        :param Optional[sqlalchemy.orm.Session] session: A pre-built session
        :rtype: Action

        Example:

        >>> from bio2bel.models import Action
        >>> Action.store_drop('hgnc')
        """
        return _store_helper(cls.make_drop, resource, session=session)

    @classmethod
    def ls(cls, session=None):
        """Get all actions.

        :param Optional[sqlalchemy.orm.Session] session: A pre-built session
        :rtype: list[Action]
        """
        session = session or _make_session()
        actions = session.query(cls).order_by(Action.created.desc()).all()
        session.close()
        return actions

    @classmethod
    def count(cls, session=None):
        """Count all actions.

        :param Optional[sqlalchemy.orm.Session] session: A pre-built session
        :rtype: int
        """
        session = session or _make_session()
        count = session.query(cls).count()
        session.close()
        return count
