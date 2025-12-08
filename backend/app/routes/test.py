from flask import Blueprint
from flask import jsonify

test_bp = Blueprint('test', __name__)


@test_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'pong'})
