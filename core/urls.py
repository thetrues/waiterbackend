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
v1.register("core/credit-customers", core_views.CreditCustomerViewSet)


# bar endpoints
v1.register("bar/regular-inventory-record", bar_views.RegularInventoryRecordViewSet)
v1.register("bar/tekila-inventory-record", bar_views.TekilaInventoryRecordViewSet)
v1.register("bar/sales/regular/items", bar_views.BarRegularItemViewSet)
v1.register("bar/sales/regular/order-records", bar_views.RegularOrderRecordViewSet)

v1.register("bar/sales/tequila/items", bar_views.BarTequilaItemViewSet)
v1.register("bar/sales/tequila/order-records", bar_views.TequilaOrderRecordViewSet)

v1.register(
    "bar/sales/regular/customer-order-records",
    bar_views.CustomerRegularOrderRecordViewSet,
)
v1.register(
    "bar/sales/regular/customer-order-payments",
    bar_views.CustomerRegularOrderRecordPaymentViewSet,
)
v1.register(
    "bar/sales/regular/credit-customer/payment-history",
    bar_views.CreditCustomerRegularOrderRecordPaymentHistoryViewSet,
)


v1.register(
    "bar/sales/tequila/customer-order-records",
    bar_views.CustomerTequilaOrderRecordViewSet,
)
v1.register(
    "bar/sales/tequila/customer-order-payments",
    bar_views.CustomerTequilaOrderRecordPaymentViewSet,
)
v1.register(
    "bar/sales/tequila/credit-customer/payment-history",
    bar_views.CreditCustomerTequilaOrderRecordPaymentHistoryViewSet,
)


v1.register(
    "bar/payrol",
    bar_views.BarPayrolViewSet,
)


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
v1.register(
    "restaurant/customer-order", restaurant_views.RestaurantCustomerOrderViewSet
)
v1.register("restaurant/customer-order-dish", restaurant_views.CustomerDishViewSet)
v1.register(
    "restaurant/customer-order-dish-payments",
    restaurant_views.CustomerDishPaymentViewSet,
)
v1.register(
    "restaurant/credit-customer/payment-history",
    restaurant_views.CreditCustomerDishPaymentHistoryViewSet,
)
v1.register(
    "restaurant/payrol",
    restaurant_views.RestaurantPayrolViewSet,
)


urlpatterns = [
    path("", include(v1.urls)),
]
