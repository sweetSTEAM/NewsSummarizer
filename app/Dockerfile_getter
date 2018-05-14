FROM ubuntu:latest

RUN apt-get update \
    && apt-get install --assume-yes \
    	htop \
    	wget \
    	python3-pip \
    	unzip
RUN pip3 install --upgrade pip
RUN pip3 install pymongo pytz requests pytz bs4

RUN mkdir app
WORKDIR /app
COPY news_getter.py ./
COPY parsers ./