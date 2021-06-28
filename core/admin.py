from django.contrib import admin
from core.models import *

models: list = [
    Item,
    InventoryRecord,
    DailyStock,
    Menu,
    Additive,
    Order,
    CompleteOrder,
]

admin.site.register(models)
