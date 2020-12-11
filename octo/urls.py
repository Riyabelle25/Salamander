from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static 
from django.conf import settings 
from scripts import views

urlpatterns = [
    path('', views.Results_toFirestore, name='home'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
