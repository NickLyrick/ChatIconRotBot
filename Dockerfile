ARG PYTHON_VERSION=3.9
ARG PYTHON_BUILD_VERSION=$PYTHON_VERSION-bookworm

FROM python:${PYTHON_BUILD_VERSION}

RUN mkdir -p /opt/src
WORKDIR /opt/src

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt update && apt -y install poppler-utils && apt clean --dry-run

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py answers.py .