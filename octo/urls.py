from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static 
from django.conf import settings 
from scripts import views
from scripts import utils

thread= utils.ThreadingExample()

urlpatterns = [

    path('', thread.thread, name='home'),

    path('scripts/',include('scripts.urls'))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
