# Deliberately bad Dockerfile — used by the `droast` skill for demos.
# Focus: Python-specific pitfalls.
# Expected rule hits (non-exhaustive):
#   DF001  :latest tag
#   DF005  unpinned requirements (flagged via surrounding context)
#   DF007  COPY . .
#   DF011  single-stage build — no slim runtime
#   DF020  no explicit non-root USER
#   DF025  shell-form CMD
#   DF030  pip install without --no-cache-dir
#   DF032  PYTHONDONTWRITEBYTECODE / PYTHONUNBUFFERED not set
#   DF036  consider HEALTHCHECK for long-running web app

FROM python:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD python -m app
