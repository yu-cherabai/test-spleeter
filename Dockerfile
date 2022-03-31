FROM python:3.8

WORKDIR /app

COPY . /app

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y ffmpeg
RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD celery -A src.celery_tasks.celery worker -l INFO --pool solo -D && uvicorn src.main:app --host 0.0.0.0
