#!/bin/bash

if [ ! -f /bootstrap/.bootstrapped_mon ]
then
        mv /bootstrap/* /conf/
        echo 1 > /bootstrap/.bootstrapped_mon
fi

cd /conf/
while(true)
do
        python monitor.py 
        sleep 5
done
