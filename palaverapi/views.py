from rivr.router import Router
from rivr.http import Response


router = Router()

@router.register(r'^$')
def status(request):
    return Response(status=204)


