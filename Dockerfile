FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
COPY ./main.py /app/main.py
ENV APP_MODULE=main:app
