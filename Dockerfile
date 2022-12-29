FROM python:3.6.8

WORKDIR /opt/app

# pip install
RUN pip install --upgrade pip
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt