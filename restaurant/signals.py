from restaurant.models import MainInventoryItemRecord, MainInventoryItemRecordStockOut
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=MainInventoryItemRecord)
def set_available_quantity(sender, instance, created, **kwargs):
    if created:
        instance.available_quantity = instance.quantity
        instance.save()


@receiver(post_save, sender=MainInventoryItemRecordStockOut)
def send_notification(sender, instance, created, **kwargs):
    if (
        created
        and instance.item_record.threshold >= instance.item_record.available_quantity
    ):
        print("Sending notification to manager")
