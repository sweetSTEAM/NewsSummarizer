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
COPY news_analyzer.py ./
COPY nlp ./
COPY requirements.txt ./

RUN pip3 install -r requirements.txt
RUN mkdir -p ./nlp/models
WORKDIR /app/nlp/models
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
WORKDIR /app
CMD ["python3", "news_analyzer.py"]