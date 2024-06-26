FROM python:3.12.1-slim-bookworm
LABEL maintainer="Saff <saf@saf.saf>"

ENV INSTALL_PATH /webapp
RUN mkdir -p $INSTALL_PATH

# This is needed to install hdbscan
RUN apt-get update
RUN apt-get -y install gcc 

WORKDIR $INSTALL_PATH

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--access-logfile", "-", "webapp.app:create_app()"]
