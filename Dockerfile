FROM alpine

LABEL maintainer "Alexey Nizhegolenko <ratibor78@gmail.com>"
LABEL description "Geostat app"


# Copy the requirements file
COPY requirements.txt /tmp/requirements.txt

# Install all needed packages
RUN apk add --no-cache \
    python2 \
    bash && \
    python2 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip2 install --upgrade pip setuptools && \
    pip2 install -r /tmp/requirements.txt && \
    rm -r /root/.cache

RUN wget https://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz 
RUN mkdir tmpgeo
RUN tar -xvf GeoLite2-City.tar.gz -C ./tmpgeo 
RUN cp /tmpgeo/*/GeoLite2-City.mmdb /

# Copy the application file
ADD geoparser.py /

# Run our app using Supervisord
CMD [ "python", "./geoparser.py"]
