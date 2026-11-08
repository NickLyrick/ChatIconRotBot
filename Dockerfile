ARG PYTHON_VERSION=3.14
ARG PYTHON_BUILD_VERSION=$PYTHON_VERSION-alpine

FROM python:${PYTHON_BUILD_VERSION}

RUN mkdir -p /opt/src
WORKDIR /opt/src

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py alembic.ini ./
COPY src ./src

EXPOSE 8080
CMD ["python", "main.py"]
