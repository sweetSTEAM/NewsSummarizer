FROM ubuntu:latest

RUN apt-get update \
    && apt-get install --assume-yes \
    	htop \
    	wget \
    	python3-pip \
    	unzip
RUN pip3 install --upgrade pip
RUN pip3 install pymongo pytz requests pytz bs4 lxml

RUN mkdir app
WORKDIR /app
COPY news_getter.py ./
COPY parsers ./
CMD ["python3", "news_getter.py"]