FROM tiangolo/uvicorn-gunicorn:python3.8
WORKDIR /app/

COPY . /app/
COPY requirements.txt . 
RUN pip3 --no-cache-dir install -r requirements.txt