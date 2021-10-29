from django.db.models.aggregates import Sum
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from rest_framework import serializers

from restaurant.models import (
    CreditCustomerDishPaymentHistory,
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
    MainInventoryItemRecord, MainInventoryItemRecordTrunk,
)
from restaurant.utils import get_recipients


@receiver(post_save, sender=MainInventoryItemRecord)
def set_available_quantity_for_main_inventory(sender, instance, created, **kwargs):
    if created:
        instance.available_quantity = instance.quantity
        instance.save()
        trunk = MainInventoryItemRecordTrunk.objects.get(item=instance.main_inventory_item.item)
        trunk.inventory_items.add(instance)
        trunk.save()


@receiver(pre_delete, sender=MainInventoryItemRecord)
def del_main_inv_record(sender, instance, **kwargs):
    if instance.maininventoryitemrecordstockout_set.exists():
        raise serializers.ValidationError("Operation failed")


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

        total = CreditCustomerDishPaymentHistory.objects.filter(
            credit_customer_dish_payment=instance.credit_customer_dish_payment
        ).aggregate(total=Sum("amount_paid"))["total"]

        # obj3 = obj2.customer_dish
        if total == 0:
            obj2.payment_status = "unpaid"
        elif total >= obj2.get_total_amount_to_pay:
            obj2.payment_status = "paid"
        else:
            obj2.payment_status = "partial"

        obj2.save()
