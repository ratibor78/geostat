# GeoStat

GeoStat is a Python script for parsing Nginx and Apache logs files and getting GEO data from incoming IP's in it. This script convert parsed data in to Json format and send it to InfluxDB database so you can use them to build some nice Grafana dashboards for example. It runs as service by SystemD and parse log in "tailf" style.
# Main Features:

  - Parsing incoming ip's from web server log and convert them in to GEO metrics for   the InfluxDB.
  - Used standard python lib's for the maximus compatibility.
  - Having an external 'settings.ini' for comfortable changing parameters.
