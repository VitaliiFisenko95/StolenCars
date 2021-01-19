import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Tuple

import requests
import xlsxwriter

from stolen_cars import errors

MAX_LIMIT = 100

DECODE_VIN_URL = os.environ['VIN_DECODE_URL']
RESP_FORMAT = os.environ['RESP_FORMAT']


@dataclass
class Paginator:
    curr_page: Optional[int] = None
    prev_page: Optional[int] = None
    next_page: Optional[int] = None
    last_page: Optional[int] = None
    limit: Optional[int] = None

    def to_dict(self) -> Dict[str, Optional[int]]:
        return {
            'curr_page': self.curr_page,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'last_page': self.last_page,
            'limit': self.limit
        }

    @classmethod
    def new(cls, count: int, page: int, limit: int) -> 'Paginator':
        if not count:
            return cls()
        full_pages = count // limit
        last_page = full_pages + 1 if count % limit != 0 else full_pages
        next_page = page + 1 if page < last_page else None

        prev_page = None
        if page > last_page:
            prev_page = last_page
        elif page > 1:
            prev_page = page - 1
        return cls(page, prev_page, next_page, last_page, limit)

    @classmethod
    def as_dict_from_request(cls, request, count: int) -> Dict[str, Optional[int]]:
        page, limit = cls._get_params_from_request(request)
        return cls.new(count, page, limit).to_dict()

    @classmethod
    def _get_params_from_request(cls, request) -> Tuple[int, int]:
        page_param = int(request.args.get('page') or '1')
        page = 1 if page_param < 1 else page_param
        limit_param = int(request.args.get('limit') or '10')
        limit = 1 if limit_param < 1 else limit_param
        return page, limit


class XlsBuilder:
    def __init__(self, data):
        self.data = data
        self.headers = ('ID', 'created_at', 'updated_at', 'vin', 'color', 'name', 'car_number', 'model', 'make',
                        'production_year', 'status')

    def generate_file(self):
        file_name = os.path.join(os.path.dirname(__file__), f'{datetime.now().strftime("%Y-%m-%d-%H-%m-%S")}.xlsx')
        workbook = xlsxwriter.Workbook(file_name)
        cell_format = workbook.add_format({'bold': True})
        worksheet = workbook.add_worksheet()
        self.write_headers(worksheet, cell_format)
        row = 1
        for obj in self.data:
            self.fill_row(obj, worksheet, row)
            row += 1

        workbook.close()
        return file_name

    def write_headers(self, worksheet, header_format):
        col = 0
        for header in self.headers:
            worksheet.set_column(0, col, 30)
            worksheet.write(0, col, header, header_format)
            col += 1

    def fill_row(self, obj, worksheet, row):
        col = 0
        for value in obj.values():
            worksheet.set_column(row, col, 30)
            worksheet.write(row, col, value)
            col += 1


def _fetch_data_by_vin(vin):
    resp = requests.get(f'{DECODE_VIN_URL}/{vin}?format={RESP_FORMAT}')
    if not resp.ok:
        raise errors.VinDecodeError(vin, resp.content)
    return resp.json()


def prepare_vin_data(vin):
    data = _fetch_data_by_vin(vin)
    payload = data['Results']
    return {
        'model': payload[8]['Value'].upper(),
        'make': payload[6]['Value'].upper(),
        'production_year': payload[9]['Value'].upper()
    }


def fetch_makes():
    resp = requests.get(f'https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format={RESP_FORMAT}')
    if not resp.ok:
        raise errors.MakeFetchError(resp.content)
    yield resp.json()['Results']


def fetch_models_by_make(make):
    resp = requests.get(f'https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{make}?format={RESP_FORMAT}')
    if not resp.ok:
        raise errors.ModelFetchError(resp.content)
    yield resp.json()['Results']
