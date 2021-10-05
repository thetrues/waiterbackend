from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from bar import views as bar_views
from core import views as core_views
from restaurant import views as restaurant_views

v1 = routers.DefaultRouter()  # a router instance

# core endpoints
v1.register("core/measurement-units", core_views.MeasurementUnitViewSet)
v1.register("core/items", core_views.ItemViewSet)
v1.register("core/credit-customers", core_views.CreditCustomerViewSet)

# bar endpoints
v1.register("bar/regular-inventory-record", bar_views.RegularInventoryRecordViewSet, basename="RegularInventoryRecord")
v1.register("bar/tekila-inventory-record", bar_views.TekilaInventoryRecordViewSet, basename="TekilaInventoryRecord")
v1.register("bar/sales/regular/items", bar_views.BarRegularItemViewSet, basename="RegularInventoryRecord")
# v1.register("bar/sales/regular/order-records", bar_views.RegularOrderRecordViewSet)

# Starts
v1.register("bar/sales/order-records", bar_views.RegularTequilaOrderRecordViewSet, basename="RegularTequilaOrderRecord")
v1.register(
    "bar/sales/customer-order-records",
    bar_views.CustomerRegularTequilaOrderRecordViewSet,
    basename="CustomerRegularTequilaOrderRecord"
)
v1.register(
    "bar/sales/customer-order-payments",
    bar_views.CustomerRegularTequilaOrderRecordPaymentViewSet,
    basename="CustomerRegularTequilaOrderRecordPayment"
)
v1.register(
    "bar/sales/credit-customer/payment-history",
    bar_views.CreditCustomerRegularTequilaOrderRecordPaymentHistoryViewSet,
    basename="CreditCustomerRegularTequilaOrderRecordPaymentHistory"
)
# Ends

v1.register("bar/sales/tequila/items", bar_views.BarTequilaItemViewSet, basename="TekilaInventoryRecord")
v1.register("bar/sales/tequila/order-records", bar_views.TequilaOrderRecordViewSet, basename="TequilaOrderRecord")

# v1.register(
#     "bar/sales/regular/customer-order-records",
#     bar_views.CustomerRegularOrderRecordViewSet,
# )
# v1.register(
#     "bar/sales/regular/customer-order-payments",
#     bar_views.CustomerRegularOrderRecordPaymentViewSet,
# )
# v1.register(
#     "bar/sales/regular/credit-customer/payment-history",
#     bar_views.CreditCustomerRegularOrderRecordPaymentHistoryViewSet,
# )


v1.register(
    "bar/sales/tequila/customer-order-records",
    bar_views.CustomerTequilaOrderRecordViewSet,
    basename="CustomerTequilaOrderRecord"
)
v1.register(
    "bar/sales/tequila/customer-order-payments",
    bar_views.CustomerTequilaOrderRecordPaymentViewSet,
    basename="CustomerTequilaOrderRecordPayment"
)
v1.register(
    "bar/sales/tequila/credit-customer/payment-history",
    bar_views.CreditCustomerTequilaOrderRecordPaymentHistoryViewSet,
    basename="CreditCustomerTequilaOrderRecordPaymentHistory"
)

v1.register(
    "bar/payrol",
    bar_views.BarPayrolViewSet,
    basename="BarPayrol"
)

# restaurant endpoints
v1.register(
    "restaurant/inventory/main-inventory-item",
    restaurant_views.MainInventoryItemViewSet,
)
v1.register(
    "restaurant/inventory/main-inventory-item-record",
    restaurant_views.MainInventoryItemRecordViewSet,
    basename="MainInventoryItemRecord"
)
v1.register(
    "restaurant/inventory/miscellaneous-inventory-record",
    restaurant_views.MiscellaneousInventoryRecordViewSet,
    basename="MiscellaneousInventoryRecord"
)
v1.register("restaurant/additives", restaurant_views.AdditiveViewSet)
v1.register("restaurant/menus", restaurant_views.MenuViewSet)
v1.register(
    "restaurant/customer-order", restaurant_views.RestaurantCustomerOrderViewSet,
    basename="RestaurantCustomerOrder"
)
v1.register("restaurant/customer-order-dish", restaurant_views.CustomerDishViewSet, basename="CustomerDish")
v1.register(
    "restaurant/customer-order-dish-payments",
    restaurant_views.CustomerDishPaymentViewSet,
    basename="CustomerDishPayment"
)
v1.register(
    "restaurant/credit-customer/payment-history",
    restaurant_views.CreditCustomerDishPaymentHistoryViewSet,
    basename="CreditCustomerDishPaymentHistory"
)
v1.register(
    "restaurant/payrol",
    restaurant_views.RestaurantPayrolViewSet,
    basename="RestaurantPayrol"
)

urlpatterns = [
    path("", include(v1.urls)),
]
