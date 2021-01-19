FROM python:3-slim as prod_base
WORKDIR /stolen_cars
ENV PYTHONUNBUFFERED True
COPY requirements.txt .
RUN pip install -i https://pypi-int.prozorro.sale/ -r requirements.txt
COPY files /files

FROM prod_base as prod
COPY src/ .

FROM prod
