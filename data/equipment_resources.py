from flask_restful import Resource, abort
from . import db_session
from .equipment import Equipment
from .users import User
from flask import jsonify
from .reqparse import parser


def abort_if_news_not_found(user_id):
    session = db_session.create_session()
    equipment = session.query(Equipment).get(user_id)
    if not equipment:
        abort(404, message=f"Equipment {user_id} not found")


class NewsResource(Resource):
    def get(self, user_id):
        abort_if_news_not_found(user_id)
        session = db_session.create_session()
        equipment = session.query(Equipment).get(user_id)
        return jsonify({'news': equipment.to_dict(
            only=('title', 'content', 'user_id', 'is_private'))})
