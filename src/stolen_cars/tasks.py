import logging

from celery.schedules import crontab
from stolen_cars.celery import celery_app
from stolen_cars import db, tools
from stolen_cars.models.models import Car

LOG = logging.getLogger(__name__)


@celery_app.task(ignore_result=True)
def decode_vin(obj_id):
    with db.read_and_update(obj_id) as car:
        if car.vin:
            data = tools.prepare_vin_data(car.vin)
            car.update_car(data)
        LOG.warning(f'Object with id {car._id} has no vin')


@celery_app.task(ignore_result=True)
def monthly_update():
    data = tools.fetch_makes()
    for make_data in data:
        make = make_data['Make_Name']
        for model_data in tools.fetch_models_by_make(make):
            model = model_data['Model_Name']
            _id = db.create_object(Car({'make': make, 'model': model}))
            LOG.info(f'New object inserted id - {_id}')


celery_app.conf.beat_schedule = {
    'monthly_update': {
        'task': 'monthly_update',
        'schedule': crontab(day_of_month=1)
    },
}
