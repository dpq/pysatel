#!/bin/bash

echo Database is removing...
DBNAME=`cat /etc/pysatel.conf | grep mysqldatabase | sed s/mysqldatabase// | sed s/=// |  awk '{ print $1 }'`
USERNAME=`cat /etc/pysatel.conf | grep mysqluser | sed s/mysqluser// | sed s/=// |  awk '{ print $1 }'`
PSW=`cat /etc/pysatel.conf | grep mysqlpassword | sed s/mysqlpassword// | sed s/=// |  awk '{ print $1 }'`
echo Enter your root mysql password below.
mysql --user=root -p --execute="drop database $DBNAME; drop user $USERNAME";

echo This script asked you to let it operate as root.
sudo rm -rf /usr/local/lib/python2.5/site-packages/pysatel
sudo rm /usr/local/bin/pysatel-admin.py
sudo rm /etc/pysatel.conf
echo You should remove from crontab this line: @hourly /usr/local/lib/python2.5/site-packages/pysatel/process.py
echo Deinstallation completed successfully.
