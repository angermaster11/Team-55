FROM python:3.11-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 runner
USER runner

WORKDIR /work

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
