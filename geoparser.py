# Getting GEO information from Nginx access.log by IP's.
# Alexey Nizhegolenko 2018
# Parts added by Remko Lodder, 2019.
# Added: IPv6 matching, make query based on geoip2 instead of
# geoip, which is going away r.s.n.
# Added possibility of processing more than one Nginx log file,
# by adding threading support. 2022 July by Alexey Nizhegolenko

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
from influxdb_client import InfluxDBClient as InfluxDBClient2
from influxdb_client.client.write_api import SYNCHRONOUS
from IPy import IP as ipadd
import threading


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


def logparse(LOGPATH, WEBSITE, MEASUREMENT, GEOIPDB, INODE, INFLUXDB_VERSION,
            INFLUXHOST=None, INFLUXPORT=None, URL=None, INFLUXDBDB=None, INFLUXUSER=None,
             INFLUXUSERPASS=None, INFLUXDBTOKEN=None, INFLUXDBBUCKET=None, INFLUXDBORG=None): # NOQA
    # Preparing variables and params
    IPS = {}
    COUNT = {}
    GEOHASH = {}
    HOSTNAME = os.uname()[1]
    if INFLUXDB_VERSION == "1":
        CLIENT = InfluxDBClient(host=INFLUXHOST, port=INFLUXPORT,
                                username=INFLUXUSER, password=INFLUXUSERPASS, database=INFLUXDBDB) # NOQA
    elif INFLUXDB_VERSION == "2":
        CLIENT = InfluxDBClient2(url=URL, token=INFLUXDBTOKEN, org=INFLUXDBORG) # NOQA

    re_IPV4 = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    re_IPV6 = re.compile('(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))') # NOQA

    GI = geoip2.database.Reader(GEOIPDB)
    # Main loop that parses log file in tailf style with sending metrics out
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
                return
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
                        GEOHASH['website'] = WEBSITE
                        GEOHASH['country_code'] = INFO.country.iso_code
                        GEOHASH['country_name'] = INFO.country.name
                        GEOHASH['city_name'] = INFO.city.name
                        IPS['tags'] = GEOHASH
                        IPS['fields'] = COUNT
                        IPS['measurement'] = MEASUREMENT
                        METRICS.append(IPS)
                        # Sending json data itto InfluxDB
                        try:
                            if INFLUXDB_VERSION == "1":
                                CLIENT.write_points(METRICS)
                            elif INFLUXDB_VERSION == "2":
                                write_api = CLIENT.write_api(write_options=SYNCHRONOUS) # NOQA
                                write_api.write(INFLUXDBBUCKET, INFLUXDBORG, record=METRICS) # NOQA
                        except Exception:
                            logging.exception("Cannot establish connection with InfluxDB server: ") # NOQA


def main():
    # Preparing for reading the config file
    PWD = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    CONFIG = configparser.ConfigParser()
    CONFIG.read(f'{PWD}/settings.ini')
    # Get the InfluxDB version so we can parse only needed part of config
    INFLUXDB_VERSION = CONFIG.get('INFLUXDB_VERSION', 'version')

    if INFLUXDB_VERSION == "1":
        # Getting params from config for version 1
        GEOIPDB = CONFIG.get('GEOIP', 'geoipdb')
        LOGPATH = CONFIG.get('NGINX_LOGS', 'logpath').split()
        INFLUXHOST = CONFIG.get('INFLUXDB1', 'host')
        INFLUXPORT = CONFIG.get('INFLUXDB1', 'port')
        INFLUXDBDB = CONFIG.get('INFLUXDB1', 'database')
        INFLUXUSER = CONFIG.get('INFLUXDB1', 'username')
        MEASUREMENT = CONFIG.get('INFLUXDB1', 'measurement')
        INFLUXUSERPASS = CONFIG.get('INFLUXDB1', 'password')
    elif INFLUXDB_VERSION == "2":
        # Getting params from config for version 2
        LOGPATH = CONFIG.get('NGINX_LOGS', 'logpath').split()
        URL = CONFIG.get('INFLUXDB2', 'url')
        INFLUXDBTOKEN = CONFIG.get('INFLUXDB2', 'token')
        INFLUXDBBUCKET = CONFIG.get('INFLUXDB2', 'bucket')
        MEASUREMENT = CONFIG.get('INFLUXDB2', 'measurement')
        INFLUXDBORG = CONFIG.get('INFLUXDB2', 'organization')


    # Parsing log file and sending metrics to Influxdb
    while True:
        logs = []
        thread_names = []
        for logitem in LOGPATH:
            logs.append(logitem.split(":"))
        for website, log in logs:
            # Get inode from log file
            if os.path.exists(log):
                INODE = os.stat(log).st_ino
            else:
                logging.info('Nginx log file %s not found', log)
                print('Nginx log file %s not found' % log)
                return
            if INFLUXDB_VERSION == "1":
                # Run the main loop and grep data in separate threads
                t = website
                if os.path.exists(log):
                    t = threading.Thread(target=logparse, kwargs={'GEOIPDB': GEOIPDB, 'LOGPATH': LOGPATH, 'INFLUXHOST': INFLUXHOST,
                               'INODE': INODE, 'WEBSITE': website, 'INFLUXPORT': INFLUXPORT, 'INFLUXDBDB': INFLUXDBDB,
                               'INFLUXUSER': INFLUXUSER, 'MEASUREMENT': MEASUREMENT,
                               'INFLUXUSERPASS': INFLUXUSERPASS, 'INFLUXDB_VERSION': INFLUXDB_VERSION}, daemon=True, name=website) # NOQA
                    for thread in threading.enumerate():
                        thread_names.append(thread.name)
                    if website not in thread_names:
                        t.start()
                else:
                    logging.info('Nginx log file %s not found', log)
                    print('Nginx log file %s not found' % log)
            elif INFLUXDB_VERSION == "2":
                # Run the main loop and grep data in separate threads
                t = website
                if os.path.exists(log):
                    t = threading.Thread(target=logparse, kwargs={'LOGPATH': LOGPATH, 'URL': URL, 'INFLUXDBTOKEN': INFLUXDBTOKEN,
                               'INFLUXDBBUCKET': INFLUXDBBUCKET, 'MEASUREMENT': MEASUREMENT,
                               'INODE': INODE, 'WEBSITE': website, 'INFLUXDBORG': INFLUXDBORG}, daemon=True, name=website) # NOQA
                    for thread in threading.enumerate():
                        thread_names.append(thread.name)
                    if website not in thread_names:
                        t.start()
                else:
                    logging.info('Nginx log file %s not found', log)
                    print('Nginx log file %s not found' % log)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.exception("Exception in main(): ")
    except KeyboardInterrupt:
        logging.exception("Exception KeyboardInterrupt: ")
        sys.exit(0)
