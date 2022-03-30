FROM python:3.8

WORKDIR /app

COPY src/main.py .
COPY requirements.txt .

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y ffmpeg
RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD celery -A main.celery worker -l INFO -D && uvicorn main:app --host 0.0.0.0
