from typing import List
from django.contrib import admin
from bar.models import (
    CustomerRegularOrderRecord,
    CustomerRegularOrderRecordPayment,
    RegularInventoryRecord,
    RegularOrderRecord,
    TekilaInventoryRecord,
    CustomerRegularTequilaOrderRecord,
)

models: List = [
    RegularInventoryRecord,
    TekilaInventoryRecord,
    CustomerRegularOrderRecordPayment,
    CustomerRegularOrderRecord,
    CustomerRegularTequilaOrderRecord,
    RegularOrderRecord,
]

admin.site.register(models)
