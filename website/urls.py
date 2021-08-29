"""website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve

from website import views
from website.settings import *

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^welcome/$', views.welcome, name='welcome'),
    url(r'^welcome/#logout=(?P<logout>[1])$', views.welcome, name='welcome'),
    url(r'^USFP/', include(('USFP.urls', 'USFP'))),
    path('getAdKey/', views.getAdKey, name='getadKey'),
    path('getUserKey/', views.getUserKey, name='getUserKey'),
    url(r'^sendCheckKey/', views.sendCheckKey, name='sendCheckKey'),
    path('refreshDB/', views.refreshDB, name='refreshDB'),
    path('refreshGraph/', views.refreshGraph, name='refreshGraph'),
    path('startScrapy/', views.startScrapy,name="startScrapy"),
    url(r'^media/(?P<path>.*)', serve, {'document_root': MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)', serve, {'document_root': STATICFILES_DIRS[0]}),
]

handler404 = views.page_not_found
