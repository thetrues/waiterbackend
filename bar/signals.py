"""
This signal is for changing the item quantity inventory record.
"""
from bar.models import RegularOrderRecord, RegularInventoryRecord, TekilaInventoryRecord
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender=RegularOrderRecord)
def alter_regular_inventory_record(sender, instance, created, **kwargs):
    # sourcery skip: last-if-guard
    if created:
        ordered_item = instance.item
        ordered_quantity = instance.quantity
        regular_item_record = RegularInventoryRecord.objects.get(item=ordered_item.item)
        regular_item_record.available_quantity = (
            regular_item_record.available_quantity - int(ordered_quantity)
        )
        regular_item_record.save()
        if regular_item_record.available_quantity == 0:
            regular_item_record.stock_status = "unavailable"
            regular_item_record.date_perished = timezone.now()
            regular_item_record.save()


# @receiver(post_save, sender=RegularOrderRecord)
# def alter_tequila_inventory_record(sender, instance, created, **kwargs):
#     # sourcery skip: last-if-guard
#     if created:
#         ordered_item = instance.item
#         ordered_quantity = instance.quantity
#         tekila_item_record = TekilaInventoryRecord.objects.get(item=ordered_item)
#         tekila_item_record.available_quantity = (
#             tekila_item_record.available_quantity - int(ordered_quantity)
#         )
#         if tekila_item_record.available_quantity == 0:
#             tekila_item_record.stock_status = "unavailable"
#             tekila_item_record.date_perished = timezone.now()
#         tekila_item_record.save()


@receiver(post_save, sender=TekilaInventoryRecord)
def set_tekila_available_quantity(sender, instance, created, **kwargs):
    # sourcery skip: last-if-guard
    if created:
        instance.available_quantity = instance.total_shots_per_tekila
        instance.save()


@receiver(post_save, sender=RegularInventoryRecord)
def set_regular_available_quantity(sender, instance, created, **kwargs):
    # sourcery skip: last-if-guard
    if created:
        instance.available_quantity = instance.total_items
        instance.save()