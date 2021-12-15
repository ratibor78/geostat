# Getting GEO information from Nginx access.log by IP's.
# Alexey Nizhegolenko 2018
# Parts added by Remko Lodder, 2019.
# Added: IPv6 matching, make query based on geoip2 instead of
# geoip, which is going away r.s.n.

import os
import re
import sys
import time
import geohash
import logging
import logging.handlers
import geoip2.database
import configparser
from influxdb import InfluxDBClient
from IPy import IP as ipadd

import glob
class SyslogBOMFormatter(logging.Formatter):
    def format(self, record):
        result = super().format(record)
        return "ufeff" + result


handler = logging.handlers.SysLogHandler('/dev/log')
formatter = SyslogBOMFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger(__name__)
root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
root.addHandler(handler)

def logparse(LOGPATH, INFLUXHOST, INFLUXPORT, INFLUXDBDB, INFLUXUSER, INFLUXUSERPASS, MEASUREMENT, GEOIPDB, INODE): # NOQA
    # Preparing variables and params
    IPS = {}
    COUNT = {}
    GEOHASH = {}
    HOSTNAME = os.uname()[1]
    CLIENT = InfluxDBClient(host=INFLUXHOST, port=INFLUXPORT,
                            username=INFLUXUSER, password=INFLUXUSERPASS, database=INFLUXDBDB) # NOQA

    re_IPV4 = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    re_IPV6 = re.compile('(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))') # NOQA

    GI = geoip2.database.Reader(GEOIPDB)

    # Main loop to parse access.log file in tailf style with sending metrcs
    with open(LOGPATH, "r") as FILE:
        STR_RESULTS = os.stat(LOGPATH)
        ST_SIZE = STR_RESULTS[6]
        FILE.seek(ST_SIZE)
        while True:
            METRICS = []
            WHERE = FILE.tell()
            LINE = FILE.readline()
            INODENEW = os.stat(LOGPATH).st_ino
            if INODE != INODENEW:
                break
            if not LINE:
                time.sleep(1)
                FILE.seek(WHERE)
            else:
                if re_IPV4.match(LINE):
                    m = re_IPV4.match(LINE)
                    IP = m.group(1)
                elif re_IPV6.match(LINE):
                    m = re_IPV6.match(LINE)
                    IP = m.group(1)

                if ipadd(IP).iptype() == 'PUBLIC' and IP:
                    INFO = GI.city(IP)
                    if INFO is not None:
                        HASH = geohash.encode(INFO.location.latitude, INFO.location.longitude) # NOQA
                        COUNT['count'] = 1
                        GEOHASH['geohash'] = HASH
                        GEOHASH['host'] = HOSTNAME
                        GEOHASH['country_code'] = INFO.country.iso_code
                        GEOHASH['country_name'] = INFO.country.name
                        GEOHASH['city_name'] = INFO.city.name
                        IPS['tags'] = GEOHASH
                        IPS['fields'] = COUNT
                        IPS['measurement'] = MEASUREMENT
                        METRICS.append(IPS)

                        # Sending json data to InfluxDB
                        try:
                            CLIENT.write_points(METRICS)
                        except Exception:
                            logging.exception("Cannot establish connection with InfluxDB server: ") # NOQA


def main():
    # Preparing for reading config file
    PWD = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    CONFIG = configparser.ConfigParser()
    CONFIG.read('%s/settings.ini' % PWD)

    # Getting params from config
    GEOIPDB = CONFIG.get('GEOIP', 'geoipdb')
    LOGPATH = CONFIG.get('NGINX_LOG', 'logpath')
    INFLUXHOST = CONFIG.get('INFLUXDB', 'host')
    INFLUXPORT = CONFIG.get('INFLUXDB', 'port')
    INFLUXDBDB = CONFIG.get('INFLUXDB', 'database')
    INFLUXUSER = CONFIG.get('INFLUXDB', 'username')
    MEASUREMENT = CONFIG.get('INFLUXDB', 'measurement')
    INFLUXUSERPASS = CONFIG.get('INFLUXDB', 'password')

    # Parsing log file and sending metrics to Influxdb
    while True:
        files = glob.glob(LOGPATH)
        for fileName in files:
            # Get inode from log file
            INODE = os.stat(fileName).st_ino
            # Run main loop and grep a log file
            if os.path.exists(fileName):
                logparse(fileName, INFLUXHOST, INFLUXPORT, INFLUXDBDB, INFLUXUSER, INFLUXUSERPASS, MEASUREMENT, GEOIPDB, INODE) # NOQA
            else:
                logging.info('Nginx log file %s not found', LOGPATH)
                print('Nginx log file %s not found' % LOGPATH)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.exception("Exception in main(): ")
    except KeyboardInterrupt:
        logging.exception("Exception KeyboardInterrupt: ")
        sys.exit(0)
