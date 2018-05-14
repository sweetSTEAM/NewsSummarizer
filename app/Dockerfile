FROM ubuntu:latest

RUN apt-get update \
    && apt-get install --assume-yes \
    	htop \
    	wget \
    	python3-pip \
    	unzip
RUN pip3 install --upgrade pip

RUN mkdir app
WORKDIR /app
COPY *.py ./
COPY frontend ./
COPY parsers ./
COPY nlp ./
COPY requirements.txt ./

RUN pip3 install -r requirements.txt

RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
WORKDIR /app