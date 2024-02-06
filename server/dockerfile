 
FROM python:latest

WORKDIR /usr/src/server

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN apt update && apt install ffmpeg libsm6 libxext6 -y
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install ./google-chrome-stable_current_amd64.deb -y

EXPOSE 5000

COPY . .

CMD [ "python", "./api.py" ]

