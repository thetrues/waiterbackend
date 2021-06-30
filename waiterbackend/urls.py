"""waiterbackend URL Configuration"""
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
# from waiterbackend.api import router

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("user.urls")),
    path("w/api/", include("core.urls")),
    # path("api/v1/", include(router.urls)),
]
