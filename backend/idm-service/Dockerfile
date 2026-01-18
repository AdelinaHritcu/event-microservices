FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto ./proto
COPY app ./app

RUN python -m grpc_tools.protoc -I ./proto \
  --python_out=./app \
  --grpc_python_out=./app \
  ./proto/idm.proto

ENV PYTHONPATH=/app:/app/app

CMD ["python", "-m", "app.server"]
