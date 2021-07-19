from django.contrib import admin
from restaurant.models import *

models: list = [
    MainInventoryItem,
    MainInventoryItemRecord,
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
    Menu,
    Additive,
    RestaurantCustomerOrder,
    CustomerDish,
    CustomerDishPayment,
]


admin.site.register(models)
