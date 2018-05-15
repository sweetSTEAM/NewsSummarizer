# Install
```
sudo apt install docker.io
sudo docker login -u ... -p ...
sudo pip install docker-compose
cd app/analyzer/nlp/models && wget "https://www.dropbox.com/sh/8s9qfy5rf1o5bbd/AAAVSVQZorVr6JH8LPJQX9tva?dl=1" -O models.zip && unzip models.zip -x /

```

# Usage
```
cd app
sudo docker-compose build
sudo docker-compose up -d
sudo docker-compose logs -f
```