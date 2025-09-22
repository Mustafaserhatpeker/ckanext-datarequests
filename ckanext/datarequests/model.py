import datetime
import uuid

from sqlalchemy import (
    Table, Column, types, ForeignKey
)
from sqlalchemy.orm import mapper, relationship, class_mapper
from sqlalchemy.orm.exc import UnmappedClassError
from ckan.model import meta
from ckan.model.domain_object import DomainObject
from ckan.model.user import User

metadata = meta.metadata


def make_uuid():
    return str(uuid.uuid4())


datarequest_table = Table(
    'data_request', metadata,
    Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
    Column('title', types.UnicodeText, nullable=False),
    Column('description', types.UnicodeText, nullable=False),
    Column('status', types.Unicode(16), nullable=False, default=u'open'),
    Column('user_id', types.UnicodeText,
           ForeignKey('user.id'), nullable=False),
    Column('created_at', types.DateTime,
           default=datetime.datetime.utcnow, nullable=False),
    Column('updated_at', types.DateTime, default=datetime.datetime.utcnow,
           onupdate=datetime.datetime.utcnow, nullable=False),
)

datarequest_comment_table = Table(
    'data_request_comment', metadata,
    Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
    Column('data_request_id', types.UnicodeText, ForeignKey(
        'data_request.id', ondelete="CASCADE"), nullable=False),
    Column('user_id', types.UnicodeText,
           ForeignKey('user.id'), nullable=False),
    Column('content', types.UnicodeText, nullable=False),
    Column('created_at', types.DateTime,
           default=datetime.datetime.utcnow, nullable=False),
)


class DataRequest(DomainObject):
    pass


class DataRequestComment(DomainObject):
    pass


def _map():
    """Map modelleri yalnızca 1 kere yap."""
    try:
        class_mapper(DataRequest)
    except UnmappedClassError:
        mapper(DataRequest, datarequest_table, properties={
            'creator': relationship(User, primaryjoin=(datarequest_table.c.user_id == User.id), lazy='joined'),
            'comments': relationship(
                lambda: DataRequestComment,
                primaryjoin=(
                    datarequest_comment_table.c.data_request_id == datarequest_table.c.id),
                order_by=datarequest_comment_table.c.created_at.asc(),
                cascade="all, delete-orphan",
                backref="data_request"
            ),
        })

    try:
        class_mapper(DataRequestComment)
    except UnmappedClassError:
        mapper(DataRequestComment, datarequest_comment_table, properties={
            'author': relationship(User, primaryjoin=(datarequest_comment_table.c.user_id == User.id), lazy='joined'),
        })


def setup():
    # Create tables if they don't exist and map models
    if not datarequest_table.exists(bind=meta.engine):
        datarequest_table.create(bind=meta.engine)
    if not datarequest_comment_table.exists(bind=meta.engine):
        datarequest_comment_table.create(bind=meta.engine)
    _map()
