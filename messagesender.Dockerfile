FROM python:3.11-bookworm
MAINTAINER me+docker@seth0r.net

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt-get update
RUN apt-get dist-upgrade -y
RUN apt-get -y install vim-nox gpg wget gnupg2 curl procps python3-all

ENV LOGLEVEL    INFO
ENV TPLDIR      /srv/tpl

WORKDIR /srv

# venv
ENV VIRTUAL_ENV=/code/venv

# python setup
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# upgrade pip
RUN pip install --upgrade pip

COPY messagesender /srv
COPY tsdb /srv/tsdb

RUN pip install -r requirements.txt

CMD ["./msgsender.py"]
