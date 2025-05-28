FROM python:3.12-bookworm
MAINTAINER me+docker@seth0r.net

RUN apt-get update
RUN apt-get dist-upgrade -y
RUN apt-get -y install vim gpg wget gnupg2 curl procps

EXPOSE 17485

ENV TMPSTOR /tmpstor
ENV PORT 17485
ENV RECVTHREADS 128

WORKDIR /code

# venv
ENV VIRTUAL_ENV=/code/venv

# python setup
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# upgrade pip
RUN pip install --upgrade pip

COPY xmlcollect-receiver /code
COPY tsdb /code/tsdb

RUN pip install -r requirements.txt

CMD ["./main.py"]
