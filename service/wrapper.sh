#!/bin/bash

LOG_FILE="/var/log/scada_early_start.log"

# Add timestamp
date >> $LOG_FILE

# Get 3 top processes snapshots
for i in {1..3}; do
    echo "Top processes snapshot $i:" >> $LOG_FILE
    top -b -n 1 | head -n 17 >> $LOG_FILE
    sleep .5
done

# Check filesystem stats
echo "Filesystem status:" >> $LOG_FILE
df -h >> $LOG_FILE

# Check I/O wait time 
echo "I/O wait status:" >> $LOG_FILE
iostat -x 1 1 >> $LOG_FILE

# Test actually reading critical files
echo "Testing .env file read:" >> $LOG_FILE
if [ -f /home/pi/gw-scada-spaceheat-python/.env ]; then
    if read -t 5 line < /home/pi/gw-scada-spaceheat-python/.env; then
        echo "Successfully read from .env file" >> $LOG_FILE
    else
        echo "FAILED to read from .env file within 5 seconds" >> $LOG_FILE
    fi
else 
    echo ".env file not found" >> $LOG_FILE
fi


# Start the Python process
exec /home/pi/gw-scada-spaceheat-python/gw_spaceheat/venv/bin/python \
    /home/pi/gw-scada-spaceheat-python/gw_spaceheat/run_scada.py