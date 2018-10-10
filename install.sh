#! /usr/bin/env bash

##
## Installetion for GeoStat script
##

echo "Creating virtual ENV and installing requirements..."

virtualenv venv && source venv/bin/activate

pip install -r requirements.txt

cp settings.ini.back settings.ini

"${VISUAL:-"${EDITOR:-vi}"}" "settings.ini"

while read line
do
    eval echo "$line"
done < "./geostat.service.template" > /lib/systemd/system/geostat.service

systemctl enable geostat.service

echo "All done, now you can start getting GEO data from your log"
echo "run 'systemd start geostat.service' "
echo "Good Luck"
