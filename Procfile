web: gunicorn -w 3 palaverapi:wsgi
worker: rqworker -q --logging_level WARNING -u $REDIS_URL
