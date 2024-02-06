FROM python:latest

WORKDIR /usr/src/server

# Install Chrome dependencies, and download Chrome itself
RUN apt-get update -y \
	&& apt-get install ffmpeg libsm6 libxext6 -y \
	&& wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
	&& apt-get install ./google-chrome-stable_current_amd64.deb -y \
	&& rm ./google-chrome-stable_current_amd64.deb \
	&& rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD [ "python", "./api.py" ]
