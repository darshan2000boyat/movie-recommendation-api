FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# Copy your FastAPI app
COPY ./main.py /app/main.py

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Point Gunicorn/Uvicorn to main.py:app
ENV APP_MODULE=main:app
