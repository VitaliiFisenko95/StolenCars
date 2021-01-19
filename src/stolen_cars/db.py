import logging
import os
from contextlib import contextmanager
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient, DESCENDING, ASCENDING

from stolen_cars import errors
from stolen_cars.models import models

DB_WRITE_CONCERN = os.getenv('MONGO_WRITE_CONCERN', 'majority')
DB_CONNECTION = None
DATABASE = None

DB_INDEXES = [
    {'keys': [('vin', DESCENDING)]},  # As I know vin must be unique, but not sure in stolen cars case
    {'keys': [('make', DESCENDING)]},
    {'keys': [('model', DESCENDING)]},
    {'keys': [('car_number', DESCENDING)]}

]

LOG = logging.getLogger(__name__)


def connection():
    global DB_CONNECTION
    if DB_CONNECTION is None:
        mongo_url = os.environ['MONGO_URL']
        DB_CONNECTION = MongoClient(mongo_url, w=DB_WRITE_CONCERN)
    return DB_CONNECTION


def db():
    global DATABASE
    if DATABASE is None:
        mongo_database = os.environ['MONGO_DATABASE']
        DATABASE = connection()[mongo_database]
    return DATABASE


def create_indexes():
    global DB_INDEXES
    for index in DB_INDEXES:
        db().stolen_cars.create_index(**index, background=True)


def create_object(obj):
    data = obj.to_native()
    current_datetime = datetime.now()
    data['created_at'] = current_datetime
    result = db().stolen_cars.insert_one(data)
    return str(result.inserted_id)


def read_object(obj_id):
    _id = ObjectId(obj_id)
    obj = db().stolen_cars.find_one({'_id': _id})
    if not obj:
        raise errors.ObjectNotFound(_id)
    return _serialize_object(obj)


def _serialize_object(data):
    try:
        return models.Car.trusted_load(data)
    except Exception as ex:
        LOG.exception("Failed to deserialize object")
        raise errors.ProcedureDeserializationError(_id=data['_id'], ex_text=str(ex))


def _update(obj):
    data = obj.to_native()
    data['updated_at'] = datetime.now()
    db().stolen_cars.find_one_and_replace(
        {
            '_id': ObjectId(data['_id']),
        },
        data
    )


@contextmanager
def read_and_update(obj_id):
    obj = read_object(obj_id)
    yield obj
    _update(obj)


def count_objects():
    return db().stolen_cars.count_documents({})


def read_objects_list(skip, field, value, limit=10, order_field='created_at', direction='desc'):
    objects = []
    query = {field: value} if field and value else {}
    cursor = db().stolen_cars.find(query).sort(order_field, ASCENDING if direction == 'ask' else DESCENDING)
    for raw_obj in cursor.skip(skip * limit).limit(limit):
        objects.append(_serialize_object(raw_obj))
    return objects


def make_autocomplete(make):
    models = []
    cursor = db().stolen_cars.find({'make': {'$regex': '.*' + make.upper() + '.*'}})
    for raw_obj in cursor:
        models.append(raw_obj['model'])
    return models
