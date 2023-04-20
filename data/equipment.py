import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Equipment(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'inf_equipment'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    info_equipment = sqlalchemy.Column(sqlalchemy.VARCHAR, nullable=False)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))

    user = orm.relationship('User', back_populates='equipment')

    def __repr__(self):
        return f'<User:> {self.id}  <info_equipment:> {self.info_equipment}'

