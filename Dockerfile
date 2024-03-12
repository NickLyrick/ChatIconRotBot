ARG PYTHON_VERSION=3.12
ARG PYTHON_BUILD_VERSION=$PYTHON_VERSION-alpine

FROM python:${PYTHON_BUILD_VERSION}

RUN mkdir -p /opt/src
WORKDIR /opt/src

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apk add --no-cache poppler-utils

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY src ./src