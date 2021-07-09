from restaurant import views as restaurant_views
from django.conf.urls import include
from core import views as core_views
from rest_framework import routers
from bar import views as bar_views
from django.urls import path

v1 = routers.DefaultRouter()  # a router instance

# core endpoints
v1.register("core/measurement-units", core_views.MeasurementUnitViewSet)
v1.register("core/items", core_views.ItemViewSet)


# bar endpoints
v1.register("bar/regular-inventory-record", bar_views.RegularInventoryRecordViewSet)
v1.register("bar/tekila-inventory-record", bar_views.TekilaInventoryRecordViewSet)


# restaurant endpoints
v1.register(
    "restaurant/inventory/main-inventory-item",
    restaurant_views.MainInventoryItemViewSet,
)
v1.register(
    "restaurant/inventory/main-inventory-item-record",
    restaurant_views.MainInventoryItemRecordViewSet,
)
v1.register(
    "restaurant/inventory/miscellaneous-inventory-record",
    restaurant_views.MiscellaneousInventoryRecordViewSet,
)
v1.register("restaurant/additives", restaurant_views.AdditiveViewSet)
v1.register("restaurant/menus", restaurant_views.MenuViewSet)
v1.register("restaurant/customer-order", restaurant_views.RestaurantCustomerOrderViewSet)
v1.register("restaurant/customer-order-dish", restaurant_views.CustomerDishViewSet)
v1.register("restaurant/customer-order-dish-payments", restaurant_views.CustomerDishPaymentViewSet)


urlpatterns = [
    path("", include(v1.urls)),
]
