FROM python:3.8

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD uvicorn src.main:app --host 0.0.0.0
