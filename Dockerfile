FROM python:3.11.7-slim

RUN mkdir -p backend && \
	apt-get update -y && \
    apt-get upgrade -y && \
	apt-get install -y bash && \
	apt-get install -y python3-pip

COPY ./pongWorld/ ./backend/
RUN pip install -r backend/requirements.txt

ENV DJANGO_SETTINGS_MODULE=pongWorld.config.settings

WORKDIR /backend

COPY init.sh ./init.sh
RUN chmod +x ./init.sh

ENTRYPOINT ["./init.sh"]