import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Module(SqlAlchemyBase):
    __tablename__ = 'modules'

    module_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  primary_key=True, autoincrement=True)
    module_title = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')
