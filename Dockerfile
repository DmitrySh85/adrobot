FROM python:3.13-alpine

ARG UID=1000
ARG GID=1000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN addgroup -g ${GID} prod && \
    adduser -u ${UID} -G prod -s /bin/sh -D prod

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R prod:prod /app

USER prod

