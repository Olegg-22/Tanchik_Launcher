from flask_restful import Resource, abort
from . import db_session
from .equipment import Equipment
from flask import jsonify
from json import dumps


def abort_if_news_not_found(user_id):
    session = db_session.create_session()
    equipment = session.query(Equipment).get(user_id)
    if not equipment:
        abort(404, message=f"Equipment {user_id} not found")


class NewsResource_eqiupment(Resource):
    def get(self, user_id):
        abort_if_news_not_found(user_id)
        session = db_session.create_session()
        equipment = session.query(Equipment).get(user_id)
        image_equipment = equipment.image_equipment
        return jsonify(inf_equipment=str(image_equipment))
        # return jsonify({'inf_equipment': equipment.to_dict(
        #     only=('info_equipment', 'image_equipment'))})
