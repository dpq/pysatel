#!/bin/bash

echo This script asked you to let it operate as root.
sudo su

echo Package is downloading into the current directory...
git svn clone -s http://pysatel.googlecode.com/svn
nano pysatel.conf
echo Database is configuring...
DBNAME=`cat pysatel.conf | grep mysqldatabase | sed s/mysqldatabase// | sed s/=// |  awk '{ print $1 }'`
USERNAME=`cat pysatel.conf | grep mysqluser | sed s/mysqluser// | sed s/=// |  awk '{ print $1 }'`
PSW=`cat pysatel.conf | grep mysqlpassword | sed s/mysqlpassword// | sed s/=// |  awk '{ print $1 }'`
echo Enter your root mysql password below.
mysql --user=root -p --execute="create database $DBNAME; grant insert,select,create,drop on $DBNAME.* to $USERNAME identified by '$PSW'";

echo Installing files...
mv pysatel.conf /etc/
mv pysatel-admin.py /usr/local/bin/
mkdir -p /usr/local/lib/python2.5/site-packages/pysatel/telemetry
mv coord.py export.py process.py /usr/local/lib/python2.5/site-packages/pysatel/
touch /usr/local/lib/python2.5/site-packages/pysatel/telemetry/__init__.py

echo Installing cron...
crontab -l > cron.tmp
echo @hourly /usr/local/lib/python2.5/site-packages/pysatel/process.py >> cron.tmp
cat cron.tmp | crontab -
rm cron.tmp
echo Installation completed successfully.
exit # exit sudo su
