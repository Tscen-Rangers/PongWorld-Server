FROM python:3.11.7-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

ENV DJANGO_SETTINGS_MODULE=config.settings

RUN apt-get update -y && \
    apt-get upgrade -y && \
	apt-get install -y bash && \
	apt-get install -y python3-pip

COPY . .

RUN pip3 install -r requirements.txt

COPY ./start_django.sh .

EXPOSE 8000

CMD ["sh", "start_django.sh"]