# Deliberately bad Dockerfile — used by the `droast` skill for demos.
# Focus: apt/shell pitfalls.
# Expected rule hits (non-exhaustive):
#   DF003  combine RUN commands
#   DF004  clean apt cache in the same RUN layer
#   DF009  WORKDIR should use absolute path
#   DF015  apt-get install without -y
#   DF016  apt-get install without --no-install-recommends
#   DF021  wget | sh — piping remote code to shell
#   DF028  apt-get update not cache-busted with the install
#   DF034  chmod 777 — overly permissive

FROM debian:bookworm

RUN apt-get update
RUN apt-get install curl wget git
RUN apt-get install build-essential
RUN apt-get clean

WORKDIR app

RUN wget -q -O - https://example.com/installer.sh | sh

COPY entrypoint.sh /app/
RUN chmod 777 /app/entrypoint.sh

ENTRYPOINT /app/entrypoint.sh
