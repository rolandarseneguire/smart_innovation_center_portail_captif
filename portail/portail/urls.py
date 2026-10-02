# portail/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('Vancouver-montreal-Sherbrooke-longueil-Soubre-0769072597/', admin.site.urls),
    path('', include('captive_portal.urls')),
]

# Servir le CSS de l'admin et les médias en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)