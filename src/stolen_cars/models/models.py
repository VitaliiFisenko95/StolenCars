from datetime import datetime

from schematics import Model, types
from schematics.contrib.mongo import ObjectIdType
from schematics.exceptions import DataError

from stolen_cars import tools, errors


class Car(Model):
    _id = ObjectIdType(metadata={'readOnly': True})
    created_at = types.DateTimeType(metadata={'readOnly': True})
    updated_at = types.DateTimeType(metadata={'readOnly': True})
    vin = types.StringType()
    color = types.StringType()
    name = types.StringType()
    car_number = types.StringType()
    model = types.StringType()
    make = types.StringType()
    production_year = types.StringType()
    status = types.StringType(choices={'active', 'deleted'}, default='active')

    def _on_production_year_set(self, value):
        if not value:
            return
        try:
            datetime.strptime(value, '%Y')
        except ValueError:
            raise DataError({'production_year': "productionYear should match pattern '%Y'"})

    def _on_make_set(self, value):
        if not value:
            return
        if not value.isupper():
            raise DataError({'make': 'make should be uppercase'})

    def _on_model_set(self, value):
        if not value:
            return
        if not value.isupper():
            raise DataError({'model': 'model should be uppercase'})

    def update_car(self, data):
        if self.status == 'deleted':
            raise errors.ForbiddenStatusError(self._id)
        if 'status' in data:
            raise DataError({'status': "Can not be set with this endpoint. "
                                       "Please use /api/cars/:obj_id/status"})
        if 'vin' in data:
            raise DataError({'vin': "Can not be set with this endpoint. "
                                    "Please use /api/cars/:obj_id/vin"})
        self.import_data(data)

    def update_car_vin(self, data):
        if self.status == 'deleted':
            raise errors.ForbiddenStatusError(self._id)
        vin = data.pop('vin')
        if data:
            raise DataError({'vin': "This is the only field that can be updated with this endpoint"})
        if not isinstance(vin, str):
            raise DataError({'vin': f"Value must be string, but found {type(vin).__name__}"})
        self.import_data({'vin': vin})

    def update_status(self, data):
        if self.status == 'deleted':
            raise errors.ForbiddenStatusError(self._id)
        status = data.pop('status')
        if data:
            raise DataError({'status': "This is the only field that can be updated with this endpoint"})
        if not isinstance(status, str):
            raise DataError({'status': f"Value must be string, but found {type(status).__name__}"})
        self.import_data({'status': status})
