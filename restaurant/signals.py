from django.db.models.signals import post_save
from restaurant.utils import get_recipients
from django.dispatch import receiver
from restaurant.models import (
    CreditCustomerDishPaymentHistory,
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
    MainInventoryItemRecord,
)
from django.utils import timezone


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
            date_perished=timezone.localdate(),
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


def send_notif(instance, message: str):
    instance.item_record.send_notification(
        message=message,
        recipients=get_recipients(),
    )


@receiver(post_save, sender=CreditCustomerDishPaymentHistory)
def update_payment_amounts(sender, instance, created, **kwargs):
    if created:
        obj = instance.credit_customer_dish_payment
        obj.amount_paid = obj.amount_paid + instance.amount_paid
        obj.save()

        obj2 = instance.credit_customer_dish_payment.customer_dish_payment
        obj2.amount_paid = obj2.amount_paid + instance.amount_paid
        obj2.date_updated = timezone.now()
        obj2.save()
        # if obj2.customer_dish.get_total_price == 1:
        #     pass
