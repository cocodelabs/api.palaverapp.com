#!/usr/bin/env bash

mkdir -p certificates

echo "$APNS_PRIVATE_KEY" > certificates/private.pem
echo "$APNS_PUBLIC_KEY" > certificates/public.pem

echo "$APNS_PRIVATE_KEY" > certificates/production.pem
echo "$APNS_PUBLIC_KEY" >> certificates/production.pem
