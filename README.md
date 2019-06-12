# GeoStat
### Version 1.0
![Alt text](https://github.com/ratibor78/geostat/blob/master/geostat.png?raw=true "Grafana dashboard example")


GeoStat is a Python script for parsing Nginx logs files and getting GEO data from incoming IP's in it. This script converts parsed data into JSON format and sends it to the InfluxDB database so you can use it to build some nice Grafana dashboards for example. It runs as service by SystemD and parses log in tailf command style. Also, it can be run as a Docker container for the easy start.
# Main Features:

  - Parsing incoming IPS from web server log and convert them into GEO metrics for the InfluxDB.
  - Used standard python libs for maximum compatibility.
  - Having an external **settings.ini** for comfortable changing parameters.
  - Have a Docker file for quick building Docker image.

JSON format that script sends to InfluxDB looks like:
```
[
    {
        'fields': {
            'count': 1
        },
        'measurement': 'geo_cube',
        'tags': {
            'host': 'cube'
            'geohash': 'u8mb76rpv69r',
            'country_code': 'UA'
        }
     }
]
```
As you can see there are three tags fields, so you can build dashboards using geohash (with a point on the map) or country code, or build dashboards with variables based on the host name tag. A count for any metric equals 1. This script doesn't parse log file from the beginning but parses it line by line after running. So you can build dashboards using **count** of geohashes or country codes after some time will pass.

You can find the example Grafana dashboard in **geomap.json** file or from grafana.com: https://grafana.com/dashboards/8342

### Tech

GeoStat uses a number of open source libs to work properly:

* [Geohash](https://github.com/vinsci/geohash) - Python module that provides functions for decoding and encoding Geohashes.
* [InfluxDB-Python](https://github.com/influxdata/influxdb-python) - Python client for InfluxDB.

# Installation
Using install.sh script:
1) Clone the repository.
2) CD into dir and run **install.sh**, it will ask you to set a properly settings.ini parameters, like Nginx **access.log** path, and InfluxDB settings.  
3) After the script will finish you only need to start SystemD service with **systemctl start geostat.service**.

Manually:
1) Clone the repository, create an environment and install requirements
```sh
$ cd geostat
$ virtualenv venv && source venv/bin/activate
$ pip install -r requirements.txt
```
2) Modify **settings.ini** & **geostat.service** files and copy service to systemd.
```sh
$ cp settings.ini.bak settings.ini
$ vi settings.ini
$ cp geostat.service.template geostat.service
$ vi geostat.service
$ cp geostat.service /lib/systemd/system/
```
3) Download latest GeoLite2-City.mmdb from MaxMind
```sh
$ wget https://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
$ tar -xvzf GeoLite2-City.tar.gz
$ cp ./GeoLite2-City_some-date/GeoLite2-City.mmdb ./
```
4) Then enable and start service
```sh
$ systemctl enable geostat.service
$ systemctl start geostat.service
```
Using Docker image:
1) Build the docker image from the Dockerfile inside geostat repository directory run:
```
$ docker build -t some-name/geostat .
```
2) After Docker image will be created you can run it using properly edited **settings.ini** file and you also,
need to forward the Nginx/Apache logfile inside the container:
```
docker run -d --name geostat -v /opt/geostat/settings.ini:/settings.ini -v /var/log/nginx_access.log:/var/log/nginx_access.log some-name/geostat
```

After the first metrics will go to the InfluxDB you can create nice Grafana dashboards.

Have fun !

License
----

MIT

**Free Software, Hell Yeah!**
