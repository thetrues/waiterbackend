"""waiterbackend URL Configuration"""
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("user.urls")),
    path("", include("core.urls")),
]
