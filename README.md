# GeoStat
### Version 0.2
![Alt text](https://github.com/ratibor78/geostat/blob/master/geostat.png?raw=true "Grafana dashboard example")


GeoStat is a Python script for parsing Nginx and Apache logs files and getting GEO data from incoming IP's in it. This script convert parsed data in to Json format and send it to InfluxDB database so you can use it to build some nice Grafana dashboards for example. It runs as service by SystemD and parse log in "tailf" style.
# Main Features:

  - Parsing incoming ip's from web server log and convert them in to GEO metrics for   the InfluxDB.
  - Used standard python lib's for the maximus compatibility.
  - Having an external 'settings.ini' for comfortable changing parameters.

### Tech

GeoStat uses a number of open source libs to work properly:

* [Geohash](https://github.com/vinsci/geohash) - Python module that provides functions for decoding and encoding Geohashes.
* [InfluxDB-Python](https://github.com/influxdata/influxdb-python) - Python client for InfluxDB.


### Installation
Using install.sh script:
1) Clone the repository.
2) CD into dir and run 'install.sh', it will ask you to set a properly settings.ini parameters, like Nginx access.log path, and InfluxDB settings.  
3) After script will finished you only need to start SystemD service with 'systemctl start geostat.service'.

Manually:
1) Clone the repository.
```sh
$ cd geostat
$ virtualenv venv && source venv/bin/activate
$ pip install -r requirements.txt
$ cp settings.ini.bak settings.ini
```
2) Modify settings.ini & geostat.service files.
```sh
$ vi settings.ini
$ cp geostat.service.template geostat.service
$ vi geostat.service
$ cp geostat.service /lib/systemd/system/
```
3) Then enable and start service
```sh
$ systemctl enable geostat.service
$ systemctl start geostat.service
```

After first metrics will go to the InfluxDB you can create nice Grafana dashboards.

Have fun !

License
----

MIT

**Free Software, Hell Yeah!**
