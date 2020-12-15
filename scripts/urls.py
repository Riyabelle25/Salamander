from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from . import views
urlpatterns = [
    path('scrapper/',views.home , name='Scrapping Followers'),
    path('scrapper/getResults/<target>',views.getResults,name='Results'),
    url(r'^scrapper/scripts/ajax/validate_username/$', views.validate_username, name='validate_username'),
]
