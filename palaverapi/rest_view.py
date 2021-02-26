from rivr.views import View
from rivr.http import Response, ResponseNoContent, ResponseNotModified

from palaverapi.responses import RESTResponse


class RESTView(View):
    def get_last_modified(self, request):
        pass

    def get_response(self, payload=None, status=None):
        if payload is None:
            response = ResponseNoContent(status=status)
        else:
            response = RESTResponse(self.request, payload, status)

        return response

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        response = None
        last_modified = None

        if request.method.lower() in ('get', 'head'):
            last_modified = self.get_last_modified(request)
            if_last_modified = request.headers.get('IF_MODIFIED_SINCE')

            if last_modified and if_last_modified:
                if_last_modified = datetime(*parsedate(if_last_modified)[:6])
                if_last_modified_gm = timegm(if_last_modified.utctimetuple())
                last_modified_gm = timegm(last_modified.utctimetuple())

                if if_last_modified_gm >= last_modified_gm:
                    response = ResponseNotModified()

        if response is None:
            response = self.get_handler(request)(request, *args, **kwargs)

        if response is None:
            response = ResponseNoContent()
        elif not isinstance(response, Response):
            response = RESTResponse(request, response)

        if last_modified:
            response.headers['Last-Modified'] = formatdate(
                timegm(last_modified.utctimetuple())
            )

        return response
