FROM python:3.9-slim

WORKDIR /app

COPY foodgram/requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY foodgram .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]