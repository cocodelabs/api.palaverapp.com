#!/usr/bin/env bash

mkdir -p keys

AUTH_KEY=APNS_AUTH_KEY_${APNS_AUTH_KEY_ID}
echo "${!AUTH_KEY}" > keys/$APNS_AUTH_KEY_ID.pem
