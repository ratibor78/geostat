#! /usr/bin/env python


# Getting GEO information for Nginx access.log IP's.
# Alexey Nizhegolenko 2018


import os
import re
# import sys
import json
import pygeoip
# import subprocess
import Geohash
import configparser
from collections import Counter
# from datetime import datetime


def logparse(logpath):
    GI = pygeoip.GeoIP('GeoLiteCity.dat', pygeoip.const.MEMORY_CACHE)
    GETIP = r"^(?P<remote_host>[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3})"
    IPS = Counter()
    with open(logpath, "r") as file:
        for line in file:
            IP = re.search(GETIP, line).group(1)
            if IP:
                IPS[IP] += 1
    OUTPUT = []
    for KEYIP, VALUE in IPS.items():
        OUTIPS = {}
        INFO = GI.record_by_addr(KEYIP)
        if INFO is not None:
            HASH = Geohash.encode(INFO['latitude'], INFO['longitude'])
            OUTIPS['ip'] = KEYIP
            OUTIPS['geohash'] = HASH
            OUTIPS['count'] = VALUE
            OUTPUT.append(OUTIPS)

    return OUTPUT


'''
def logparse(logpath):
    GI = pygeoip.GeoIP('GeoLiteCity.dat', pygeoip.const.MEMORY_CACHE)
    GETIP = r"^(?P<remote_host>[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3})"
    OUTPUT = []
    IPS = {}
    with open(logpath, "r") as file:
        for line in file:
            IP = re.search(GETIP, line)
            if IP:
                INFO = GI.record_by_addr(IP.group(1))
                if INFO is not None:
                    HASH = Geohash.encode(INFO['latitude'], INFO['longitude'])
                    # IPS['key'] = INFO['country_code']
                    # IPS['name'] = INFO['country_name']
                    IPS['ip'] = IP.group(1)
                    IPS['geohash'] = HASH
                    # IPS['data'] = {'latitude': INFO['latitude'], 'longitude': INFO['longitude']} # NOQA
                    # IPS['latitude'] = INFO['latitude']
                    # IPS['longitude'] = INFO['longitude']
                    OUTPUT.append(IPS)
    return OUTPUT
'''


def main():
    # Set LANG ENV
    os.environ["LC_ALL"] = "C"
    # Getting params from config
    pwd = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    config = configparser.ConfigParser()
    config.read('%s/settings.ini' % pwd)
    logpath = config.get('NGINX_LOG', 'logpath')
    # Parse given log file
    IPS_IN = logparse(logpath)
    # Send result to fle
    with open('/tmp/metrics.json', 'w') as outputfile:
        json.dump(IPS_IN, outputfile, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
