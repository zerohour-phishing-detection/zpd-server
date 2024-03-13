FROM python:3.11-bookworm

WORKDIR /usr/src/server

# Install Chrome dependencies, and download Chrome itself
RUN apt-get update -y \
	&& apt-get install ffmpeg libsm6 libxext6 wget -y \
	&& wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
	&& apt-get install ./google-chrome-stable_current_amd64.deb -y \
	&& rm ./google-chrome-stable_current_amd64.deb \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install gunicorn \
	&& useradd -m zpd && chown zpd ./

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

USER zpd

COPY . .

EXPOSE 5000
CMD [ "gunicorn", "-b", "0.0.0.0", "api:app" ]
