FROM python:3.12-slim

ENV USER=appuser
ENV UID=10001
ENV GID=10001

RUN groupadd --gid ${GID} ${USER} \
 && useradd --uid ${UID} --gid ${GID} --create-home ${USER}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto ./proto
COPY app ./app

# gRPC stubs (app/idm_pb2*.py) are generated from proto/idm.proto and committed

RUN mkdir -p /app/logs \
 && chown -R ${USER}:${USER} /app

ENV PYTHONPATH=/app

USER ${USER}

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
