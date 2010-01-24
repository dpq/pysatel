#!/bin/bash

# Installing files
mv pysatel.conf /etc/
mv pysatel-admin.py /usr/local/bin/
mkdir -p /usr/local/lib/python2.5/site-packages/pysatel/telemetry
mv coord.py export.py  process.py /usr/local/lib/python2.5/site-packages/pysatel/
touch /usr/local/lib/python2.5/site-packages/pysatel/telemetry/__init__.py

# Installing cron
crontab -l > cron.tmp
echo @hourly /usr/local/lib/python2.5/site-packages/pysatel/process.py >> cron.tmp
cat cron.tmp | crontab -
rm cron.tmp

echo "1. Edit /etc/pysatel.conf to specify correct directories for data and TLE archives, and correct credentials to connect to MySQL with."
echo "2. Log on to your MySQL RDBS and create the appropriate database and user. It should look like this:"
echo "      create database pysatel;"
echo "      grant insert,select,create,drop on pysatel.* to `pysatel` identified by '1234';"
echo "Make sure the credentials you enter match those specified in the /etc/pysatel.conf file!"
