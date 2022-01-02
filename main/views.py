from threading import local
from django.shortcuts import render
from django.http.response import HttpResponse, HttpResponseRedirect
from .models import main
# Create your views here.

def index(request):
  return render(request, 'index.html', locals())

def service(request):
  return render(request, 'product_service.html', locals())

def index_en(request):
  return render(request, 'index_en.html', locals())

def service_en(request):
  return render(request, 'product_service_en.html', locals())