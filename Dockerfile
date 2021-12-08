FROM python:3.7

# System packages installation
# RUN apt-get update -y
# RUN apt install -y


# Setting Home Directory for containers
WORKDIR /app

# Creating Log Directory

# Installing python packages
COPY requirements.txt . 
RUN pip3 install -U pip && pip3 install -r requirements.txt

# Bundle app source
COPY ./main main

# Run Service
EXPOSE 8080
CMD python -m main.src.server.service