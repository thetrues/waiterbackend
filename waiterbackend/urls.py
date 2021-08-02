"""waiterbackend URL Configuration"""
from restaurant import views as restaurant_views
from django.conf.urls.static import static
from django.conf.urls import include
from bar import views as bar_views
from django.conf import settings
from django.contrib import admin
from django.urls import path

# from waiterbackend.api import router

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("", include("user.urls")),
        path("w/api/", include("core.urls")),
        path(
            "w/api/restaurant/inventory/get-items",
            restaurant_views.RestaurantInventoryItemView.as_view(),
        ),
        path(
            "w/api/bar/inventory/get-items",
            bar_views.BarInventoryItemView.as_view(),
        ),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
