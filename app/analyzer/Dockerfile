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
COPY news_analyser.py ./
COPY nlp ./
COPY requirements.txt ./

RUN pip3 install -r requirements.txt
RUN mkdir -p ./nlp/models
RUN wget "https://www.dropbox.com/sh/8s9qfy5rf1o5bbd/AAAVSVQZorVr6JH8LPJQX9tva?dl=1" \
	-O ./nlp/models/models.zip
RUN unzip ./nlp/models/models.zip -x /
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
CMD ["python3", "news_analyzer.py"]