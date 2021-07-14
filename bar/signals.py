"""
This signal is for changing the item quantity inventory record.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from bar.models import OrderRecord, RegularInventoryRecord, TekilaInventoryRecord


@receiver(post_save, sender=OrderRecord)
def alter_inventory_record(sender, instance, created, **kwargs):
    if created:
        ordered_item = instance.item
        ordered_quantity = instance.quantity
        try:
            regular_item_record = RegularInventoryRecord.objects.get(item=ordered_item)
            regular_item_record.quantity = (
                regular_item_record.quantity - ordered_quantity
            )
            regular_item_record.save()
        except RegularInventoryRecord.DoesNotExist:
            tekila_item_record = TekilaInventoryRecord.objects.get(item=ordered_item)
            tekila_item_record.quantity = (
                tekila_item_record.quantity - ordered_quantity
            )
            tekila_item_record.save()
