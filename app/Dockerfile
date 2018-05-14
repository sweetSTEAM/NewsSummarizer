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
RUN mkdir models
RUN wget "https://www.dropbox.com/sh/8s9qfy5rf1o5bbd/AAAVSVQZorVr6JH8LPJQX9tva?dl=1" \
	-O ./models/models.zip
RUN unzip ./models/models.zip -d ./models -x /
RUN rm ./models/models.zip
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"