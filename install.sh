#! /usr/bin/env bash

##
## Installetion script for GeoStat
## Alexey Nizhegolenko 2018
##
echo ""
echo "Creating virtual ENV and installing requirements..."
sleep 1
virtualenv venv && source venv/bin/activate

pip install -r requirements.txt && deactivate

echo ""
echo "Please edit settings.ini file and set right parameters..."
sleep 1
cp settings.ini.back settings.ini

"${VISUAL:-"${EDITOR:-vi}"}" "settings.ini"

echo ""
echo "Installing SystemD service..."
sleep 1
while read line
do
    eval echo "$line"
done < "./geostat.service.template" > /lib/systemd/system/geostat.service

systemctl enable geostat.service

echo ""
echo "All done, now you can start getting GEO data from your log"
echo "run 'systemctl start geostat.service' for this"
echo "Good Luck !"
