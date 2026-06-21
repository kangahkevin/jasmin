#!/bin/bash

file_to_monitor="/var/log/jasmin/messages.log"
string_to_search="PRECONDITION_FAILED"

while true; do
    if tail -n 0 -F "$file_to_monitor" | grep -q "$string_to_search"; then
        supervisorctl -u $SUPERVISOR_USERNAME -p $SUPERVISOR_PASSWORD restart jasmind
        break
    fi
    sleep 10
done