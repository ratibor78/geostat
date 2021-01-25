FROM alpine

LABEL maintainer "Alexey Nizhegolenko <ratibor78@gmail.com>"
LABEL description "Geostat application"


# Copy the requirements file
COPY requirements.txt /tmp/requirements.txt

# Install all needed packages
RUN apk add --no-cache \
    python3 \
    bash && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install -r /tmp/requirements.txt && \
    rm -r /root/.cache

# Copy the Geolite base
ADD GeoLite2-City.mmdb /

#Copy the geohash lib locally
ADD geohash /

# Copy the application file
ADD geoparser.py /

# Run our app
CMD [ "python3", "./geoparser.py"]
