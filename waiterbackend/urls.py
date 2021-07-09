"""waiterbackend URL Configuration"""
from django.conf.urls.static import static
from django.conf.urls import include
from django.conf import settings
from django.contrib import admin
from django.urls import path

# from waiterbackend.api import router

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("", include("user.urls")),
        path("w/api/", include("core.urls")),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
