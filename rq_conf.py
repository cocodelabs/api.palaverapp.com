import os
from urllib.parse import urlparse


url = urlparse(os.getenv('REDIS_URL', 'redis://localhost:6379'))
REDIS_HOST = url.hostname
REDIS_PORT = url.port
REDIS_PASSWORD = url.password
REDIS_SSL = url.scheme == 'rediss'
REDIS_SSL_CERT_REQS = None
