from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('scrapper',views.scrapper , name='Scrapping Followers'),
]
