#!/bin/bash

if [ "$(id -u)" -eq 0 ] && [ "$USER_ID" -ne 0 ]; then
    exec $APP_NICE_CMD s6-applyuidgid -u $USER_ID -g $GROUP_ID -G ${SUP_GROUP_IDS:-$GROUP_ID} "$0" "$@"
fi

exec /comskip-wrapper.sh
