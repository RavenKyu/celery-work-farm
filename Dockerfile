FROM python:3.8.6-alpine3.12

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev

ADD requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /src
ADD . /src
WORKDIR src
ENV PYTHONPATH=/src

CMD ["celery", "-A", "celery_work_farm:app", "worker", "-l", "info"]