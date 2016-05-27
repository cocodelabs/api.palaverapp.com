web: gunicorn -w 3 palaverapi:wsgi
worker: rqworker -q -u $REDISTOGO_URL
