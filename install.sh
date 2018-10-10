#! /usr/bin/env bash

##
## Installetion script for GeoStat
## Alexey Nizhegolenko 2018
##

echo "Creating virtual ENV and installing requirements..."
virtualenv venv && source venv/bin/activate
sleep 1

pip install -r requirements.txt && deactivate
sleep 1

echo "Please edit settings.ini file and set right parameters..."
cp settings.ini.back settings.ini

"${VISUAL:-"${EDITOR:-vi}"}" "settings.ini"


echo "Installing SystemD service..."
while read line
do
    eval echo "$line"
done < "./geostat.service.template" > /lib/systemd/system/geostat.service

systemctl enable geostat.service
sleep 1

echo "All done, now you can start getting GEO data from your log"
echo "run 'systemd start geostat.service' for this"
echo "Good Luck !"
