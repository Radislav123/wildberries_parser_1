import time

from django.http import HttpResponse
from django.views import View


class CheckView(View):
    url = "check/"

    def get(self, request):
        return HttpResponse(time.time())
