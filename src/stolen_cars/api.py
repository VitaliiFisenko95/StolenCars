import logging
import os

from flask import Flask, request, make_response, jsonify, send_file
from stolen_cars import db, errors, tools
from stolen_cars.models.models import Car

from stolen_cars.tasks import decode_vin

from stolen_cars.tools import XlsBuilder

IS_DEBUG = os.environ['IS_DEBUG']
LOG = logging.getLogger(__name__)
app = Flask(__name__)


@app.route('/api/ping', methods=['GET'])
def ping():
    return make_response(jsonify({'text': 'pong'}), 200)


@app.route('/api/cars', methods=['POST'])
def create_car():
    data = request.get_json()
    obj = Car(data)
    _id = db.create_object(obj)
    decode_vin.delay(str(_id))
    LOG.info(f'New object inserted id - {_id}')
    return make_response(jsonify({'_id': _id}), 201)


@app.route('/api/cars/<string:obj_id>', methods=['GET'])
def get_car(obj_id):
    car = db.read_object(obj_id)
    return make_response(jsonify({'data': car.to_primitive()}), 200)


@app.route('/api/cars/<string:obj_id>', methods=['PATCH'])
def update_car(obj_id):
    data = request.get_json()
    with db.read_and_update(obj_id) as car:
        car.update_car(data)
    return make_response(jsonify({'message': 'ok'}), 200)


@app.route('/api/cars/<string:obj_id>/vin', methods=['PATCH'])
def update_car_vin(obj_id):
    data = request.get_json()
    with db.read_and_update(obj_id) as car:
        car.update_car_vin(data)
    decode_vin.delay(str(car._id))
    return make_response(jsonify({'message': 'ok'}), 200)


@app.route('/api/cars/<string:obj_id>/status', methods=['PATCH'])
def update_car_status(obj_id):
    data = request.get_json()
    with db.read_and_update(obj_id) as car:
        car.updater_status(data)
    return make_response(jsonify({'message': 'ok'}), 200)


@app.route('/api/cars', methods=['GET'])
def cars_list():
    obj_count = db.count_objects()
    paginator = tools.Paginator.as_dict_from_request(request, obj_count)
    if not obj_count:
        return make_response(jsonify({'message': [], 'paginator': paginator}), 204)

    _skip_param = paginator['curr_page'] - 1
    direction = request.args.get('direction')
    order_field = request.args.get('order_by', 'created_at')
    value = request.args.get('value')
    field = request.args.get('field')
    list_objects = db.read_objects_list(_skip_param, field, value, paginator['limit'], order_field, direction)
    if not list_objects:
        return make_response(jsonify({'message': [], 'paginator': paginator}), 204)
    result = [obj.to_primitive() for obj in list_objects]
    return make_response(jsonify({'data': result, 'paginator': paginator}), 200)


@app.route('/api/cars/xls', methods=['GET'])
def cars_list_xls():
    obj_count = db.count_objects()
    paginator = tools.Paginator.as_dict_from_request(request, obj_count)
    if not obj_count:
        return make_response(jsonify({'message': [], 'paginator': paginator}), 204)

    _skip_param = paginator['curr_page'] - 1
    direction = request.args.get('direction')
    order_field = request.args.get('order_by', 'created_at')
    value = request.args.get('value')
    field = request.args.get('field')
    list_objects = db.read_objects_list(_skip_param, field, value, paginator['limit'], order_field, direction)
    if not list_objects:
        return make_response(jsonify({'message': [], 'paginator': paginator}), 204)
    result = [obj.to_primitive() for obj in list_objects]
    file_name = XlsBuilder(result).generate_file()
    return send_file(file_name, mimetype='xlsx', as_attachment=True, attachment_filename='cars.xlsx')


@app.route('/api/cars/make/<string:make>', methods=['GET'])
def mark_autocomplete(make):
    result = db.make_autocomplete(make)
    if not result:
        return make_response(jsonify({'message': []}), 204)
    return make_response(jsonify({'data': result}), 200)


if __name__ == '__main__':
    db.create_indexes()
    app.wsgi_app = errors.ErrorsMiddleware(app.wsgi_app)
    app.run(debug=IS_DEBUG, host='0.0.0.0', port='80')
