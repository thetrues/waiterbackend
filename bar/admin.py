from django.contrib import admin
from bar.models import RegularInventoryRecord

models: list = [RegularInventoryRecord]

admin.site.register(models)
