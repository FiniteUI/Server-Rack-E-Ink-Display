FROM python:3.13-slim

ENV DOCKER=1

WORKDIR "/app"

COPY requirements.txt .
COPY cache_file.py .
COPY display.py .
COPY epd_text.py .
COPY raspberry_pi_system_information_commands.py .
COPY waveshare_epd/ waveshare_epd/

RUN apt-get update
RUN apt-get install gcc -y
RUN apt-get install wget -y
RUN apt-get install ssh -y

RUN pip install -r requirements.txt --root-user-action ignore

#lgpio from pip or apt won't build on docker for some reason
#so we install it from here
RUN wget https://github.com/Gadgetoid/PY_LGPIO/releases/download/0.2.2.0/lgpio-0.2.2.0.tar.gz
RUN pip install lgpio-0.2.2.0.tar.gz --root-user-action ignore

CMD ["python", "-u", "display.py"]