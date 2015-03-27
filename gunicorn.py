import os
import subprocess

workers = 3

def when_ready(server):
    print('Launching rqworker')
    redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
    subprocess.Popen(['rqworker', '-u', redis_url])

