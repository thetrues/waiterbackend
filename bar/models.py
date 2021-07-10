from core.models import BaseInventory, Item
from django.db import models

# Inventory Management


class RegularInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, related_name="item", on_delete=models.CASCADE)
    total_items = models.IntegerField(default=0)
    selling_price_per_item = models.IntegerField(default=0)

    def __str__(self) -> str():
        return str(self.item)

    def estimate_sales(self):
        return self.selling_price_per_item * self.total_items

    def estimate_profit(self):
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: list = ["-id"]
        verbose_name = u"Regular Inventory Record"
        verbose_name_plural = u"Regular Inventory Records"


class TekilaInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_shots_per_tekila = models.IntegerField(default=0)
    selling_price_per_shot = models.IntegerField(default=0)

    def __str__(self):
        return self.item.name

    def estimate_sales(self):
        return self.selling_price_per_shot * self.total_shots_per_tekila

    def estimate_profit(self):
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: list = ["-id"]
        verbose_name = u"Tekila Inventory Record"
        verbose_name_plural = u"Tekila Inventory Records"


# Sale Management
