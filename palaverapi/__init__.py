from rivr.wsgi import WSGIHandler
from palaverapi.views import router

wsgi = WSGIHandler(router)

