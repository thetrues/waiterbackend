"""waiterbackend URL Configuration"""
from reports import restaurant_views as reports_restaurant_views
from reports import bar_views as reports_bar_views
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
        # Reports Restaurant
        path(
            "w/api/restaurant/reports/get-daily-report",
            reports_restaurant_views.DailyReport.as_view(),
        ),
        path(
            "w/api/restaurant/reports/get-monthly-report",
            reports_restaurant_views.MonthlyReport.as_view(),
        ),
        path(
            "w/api/restaurant/reports/get-custom-report",
            reports_restaurant_views.CustomDateReport.as_view(),
        ),
        # Reports Bar
        path(
            "w/api/bar/reports/get-daily-report",
            reports_bar_views.DailyReport.as_view(),
        ),
        path(
            "w/api/bar/reports/get-monthly-report",
            reports_bar_views.MonthlyReport.as_view(),
        ),
        path(
            "w/api/bar/reports/get-custom-report",
            reports_bar_views.CustomDateReport.as_view(),
        ),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
