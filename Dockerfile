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

# Download Geolite base
RUN wget https://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz && \ 
    mkdir tmpgeo && tar -xvf GeoLite2-City.tar.gz -C ./tmpgeo && \ 
    cp /tmpgeo/*/GeoLite2-City.mmdb / && rm -rf ./tmpgeo

# Copy the application file
ADD geoparser.py /

# Run our app
CMD [ "python", "./geoparser.py"]
