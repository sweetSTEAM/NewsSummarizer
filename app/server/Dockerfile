FROM ubuntu:latest

RUN apt-get update \
    && apt-get install --assume-yes \
    	htop \
    	wget \
    	python3-pip \
    	unzip
RUN pip3 install --upgrade pip
RUN pip3 install flask pymongo

RUN mkdir app
WORKDIR /app
COPY server.py ./
COPY frontend ./

EXPOSE 80