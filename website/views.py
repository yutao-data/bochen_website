from django.http.response import HttpResponse, HttpResponseRedirect

def hello(request):
    return HttpResponseRedirect('/main/index')