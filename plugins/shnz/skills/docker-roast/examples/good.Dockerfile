# Reference "good" Dockerfile — used by the `droast` skill for before/after demos.
# Aims to pass the common rules:
#   DF001  specific base-image tag
#   DF002  non-root USER
#   DF003  combined RUN layers
#   DF004  apt cache cleaned in the same layer
#   DF005  pinned versions
#   DF007  targeted COPY (no COPY . .)
#   DF011  multi-stage build
#   DF012  HEALTHCHECK set
#   DF015/16  -y + --no-install-recommends
#   DF017  ENTRYPOINT + CMD
#   DF020  explicit USER
#   DF022  EXPOSE documented
#   DF025  JSON-array CMD/ENTRYPOINT
#   DF030  pip --no-cache-dir
#   DF032  PYTHONDONTWRITEBYTECODE / PYTHONUNBUFFERED

# syntax=docker/dockerfile:1.6
ARG PYTHON_VERSION=3.12.4

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl=7.88.1-10+deb12u7 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser src/ ./src/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/health || exit 1

ENTRYPOINT ["python", "-m"]
CMD ["src.app"]
