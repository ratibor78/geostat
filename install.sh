#! /usr/bin/env bash

##
## Installation script for GeoStat
## Alexey Nizhegolenko 2018
##

WORKDIR=$(pwd)

echo ""
echo "Creating virtual ENV and install all needed requirements..."
sleep 1
python3 -m venv venv && source venv/bin/activate

pip3 install -r requirements.txt && deactivate

echo ""
echo "Please edit settings.ini file and set the needed parameters..."
sleep 1
cp settings.ini.back settings.ini

"${VISUAL:-"${EDITOR:-vi}"}" "settings.ini"

echo ""
echo "Installing GeoStat SystemD service..."
sleep 1
while read line
do
    eval echo "$line"
done < "./geostat.service.template" > /lib/systemd/system/geostat.service

systemctl enable geostat.service

echo ""
echo "Last step, you need to register and download the lates GeoLite2 City mmdb file from the maxmind.com website"
echo "After you get an account on the maxmind.com you can find the needed file by the link below"
echo "https://www.maxmind.com/en/accounts/YOURACCOUNTID/geoip/downloads"
echo "Please don't forget to unzip and put the GeoLite2-City.mmdb file in the same directory with the geoparse.py"
echo "script, or you can put it enywhere and then change the way in the settings.ini"

echo ""
echo "Good, all was done and you can start getting GEO data from your Nginx/Apache log file now"
echo "Please run 'systemctl start geostat.service' for starting the GeoStat script"
echo "You can find the GeoStat application logs in the syslog file if you need"
echo "Good Luck !"
