import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Word(SqlAlchemyBase):
    __tablename__ = 'words'
    word_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                                autoincrement=True)
    word = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    translation = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    module_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey("modules.module_id"))
    module = orm.relationship('Module')
