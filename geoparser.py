#! /usr/bin/env python

# Getting GEO information for Nginx access.log IP's.
# Alexey Nizhegolenko 2018

import os
import re
# import sys
import time
# import json
import pygeoip
# import subprocess
import Geohash
import configparser
# from collections import Counter
# from datetime import datetime


def logparse(logpath):
    GI = pygeoip.GeoIP('GeoLiteCity.dat', pygeoip.const.MEMORY_CACHE)
    GETIP = r"^(?P<remote_host>[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3})"
    IPS = {}
    with open(logpath, "r") as FILE:
        STR_RESULTS = os.stat(logpath)
        ST_SIZE = STR_RESULTS[6]
        FILE.seek(ST_SIZE)
        while 1:
            WHERE = FILE.tell()
            LINE = FILE.readline()
            if not LINE:
                time.sleep(1)
                FILE.seek(WHERE)
            else:
                IP = re.search(GETIP, LINE).group(1)
                if IP:
                    INFO = GI.record_by_addr(IP)
                    if INFO is not None:
                        HASH = Geohash.encode(INFO['latitude'], INFO['longitude']) # NOQA
                        IPS['count'] = 1
                        IPS['geohash'] = HASH


def main():
    # Getting params from config
    pwd = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    config = configparser.ConfigParser()
    config.read('%s/settings.ini' % pwd)
    logpath = config.get('NGINX_LOG', 'logpath')
    # Parse given log file and send metrics
    logparse(logpath)
    # Send result to fle
    # with open('/tmp/metrics.json', 'w') as outputfile:
    #    json.dump(IPS_IN, outputfile, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
