from django.contrib import admin
from bar.models import RegularInventoryRecord, TekilaInventoryRecord

models: list = [RegularInventoryRecord, TekilaInventoryRecord]

admin.site.register(models)
