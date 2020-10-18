web: gunicorn -w 3 palaverapi:wsgi
worker: rqworker -q -u $REDIS_URL
