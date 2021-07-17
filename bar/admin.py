from django.contrib import admin
from bar.models import (
    CustomerRegularOrderRecord,
    CustomerRegularOrderRecordPayment,
    RegularInventoryRecord,
    RegularOrderRecord,
    TekilaInventoryRecord,
)

models: list = [
    RegularInventoryRecord,
    TekilaInventoryRecord,
    CustomerRegularOrderRecordPayment,
    CustomerRegularOrderRecord,
    RegularOrderRecord,
]

admin.site.register(models)
