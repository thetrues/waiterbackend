from django.db.models.signals import post_save
from restaurant.models import (
    MainInventoryItemRecord,
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
)
from django.dispatch import receiver
from datetime import datetime


@receiver(post_save, sender=MainInventoryItemRecord)
def set_available_quantity_for_main_inventory(sender, instance, created, **kwargs):
    if created:
        instance.available_quantity = instance.quantity
        instance.save()


@receiver(post_save, sender=MiscellaneousInventoryRecord)
def set_update_misc_inventory(sender, instance, created, **kwargs):
    if created:
        instance.available_quantity = instance.quantity
        instance.save()
        # Set all the previous misc items to unavailable
        MiscellaneousInventoryRecord.objects.filter(
            item=instance.item, stock_status="available"
        ).exclude(pk=instance.pk).update(
            stock_status="unavailable",
            available_quantity=0,
            date_perished=datetime.today(),
        )


@receiver(post_save, sender=MainInventoryItemRecordStockOut)
def send_notification(sender, instance, created, **kwargs):
    if (
        created
        and instance.item_record.threshold >= instance.item_record.available_quantity
    ):
        print("Sending notification to manager")
