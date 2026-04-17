# Deliberately bad Dockerfile — used by the `droast` skill for demos.
# Expected rule hits (non-exhaustive):
#   DF001  :latest tag
#   DF003  multiple RUN layers
#   DF004  apt cache not cleaned in same layer
#   DF005  unpinned package versions
#   DF007  COPY . . (entire build context)
#   DF015  apt-get install without -y
#   DF016  apt-get install without --no-install-recommends
#   DF020  no explicit non-root USER
#   DF025  shell-form CMD
#   DF028  apt-get update not cache-busted

FROM ubuntu:latest

RUN apt-get update
RUN apt-get install nginx
RUN apt-get install curl

COPY . /app
WORKDIR /app

EXPOSE 80

CMD nginx -g "daemon off;"
