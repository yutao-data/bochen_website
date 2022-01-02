from django.urls import path

from . import views

urlpatterns = [
    path('index', views.index, name='index'), 
    path('service', views.service, name='service'), 
    path('index_en', views.index_en, name='index_en'), 
    path('service_en', views.service_en, name='service_en'), 
]