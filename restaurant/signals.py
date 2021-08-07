from django.db.models.signals import post_save
from restaurant.utils import get_recipients
from django.dispatch import receiver
from restaurant.models import (
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
    MainInventoryItemRecord,
)
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
        # Send notification
        message: str = (
            "{} is nearly out of stock. The remained quantity is {} {}".format(
                instance.item_record.main_inventory_item.item.name,
                instance.item_record.available_quantity,
                instance.item_record.main_inventory_item.item.unit.name,
            )
        )
        send_notif(instance, message)

    # if instance.item_record.available_quantity == 0:
    #     item_record = instance.item_record
    #     item_record.stock_status = "unavailable"
    #     item_record.save()
    #     # Send notification
    #     message: str = "{} is out of stock. The remained quantity is {} {}".format(
    #         instance.item_record.main_inventory_item.item.name,
    #         instance.item_record.available_quantity,
    #         instance.item_record.main_inventory_item.item.unit.name,
    #     )

    #     send_notif(instance, message)


def send_notif(instance, message: str):
    instance.item_record.send_notification(
        message=message,
        recipients=get_recipients(),
    )
