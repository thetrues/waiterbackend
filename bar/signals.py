"""
This signal is for changing the item quantity inventory record.
"""
from django.db.models.aggregates import Sum
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from rest_framework import serializers

from bar.models import (
    CreditCustomerRegularTequilaOrderRecordPaymentHistory,
    RegularInventoryRecord,
    TekilaInventoryRecord,
    RegularInventoryRecordsTrunk, TequilaInventoryRecordsTrunk,
)


@receiver(post_save, sender=TekilaInventoryRecord)
def set_tekila_available_quantity(sender, instance, created, **kwargs):
    # sourcery skip: last-if-guard
    if created:
        instance.available_quantity = instance.total_shots_per_tekila
        instance.save()


@receiver(pre_delete, sender=TekilaInventoryRecord)
def pre_del_tequila_inv_record(sender, instance, **kwargs):
    if instance.tequilaorderrecord_set.exists():
        raise serializers.ValidationError("Operation failed")


@receiver(post_save, sender=RegularInventoryRecord)
def set_regular_available_quantity(sender, instance, created, **kwargs):
    if created:
        instance.available_quantity = instance.total_items
        instance.save()


@receiver(pre_delete, sender=RegularInventoryRecord)
def pre_del_regular_inv_record(sender, instance, **kwargs):
    if instance.regularorderrecord_set.exists():
        raise serializers.ValidationError("Operation failed")


@receiver(post_save, sender=RegularInventoryRecord)
def regular_inventory_trunk(sender, instance, created, **kwargs):
    if created:
        trunk = RegularInventoryRecordsTrunk.objects.get(item=instance.item)
        trunk.regular_inventory_record.add(instance)
        trunk.updated_at = timezone.now()
        trunk.save()


@receiver(post_save, sender=TekilaInventoryRecord)
def tequila_inventory_trunk(sender, instance, created, **kwargs):
    if created:
        trunk = TequilaInventoryRecordsTrunk.objects.get(item=instance.item)
        trunk.tequila_inventory_record.add(instance)
        trunk.updated_at = timezone.now()
        trunk.save()


@receiver(post_save, sender=CreditCustomerRegularTequilaOrderRecordPaymentHistory)
def update_payment_amounts(sender, instance, created, **kwargs):
    if created:
        obj = instance.credit_customer_payment
        obj.amount_paid = obj.amount_paid + instance.amount_paid
        obj.save()

        obj2 = instance.credit_customer_payment.record_order_payment_record
        obj2.amount_paid = obj2.amount_paid + instance.amount_paid
        obj2.date_updated = timezone.now()
        obj2.save()

        total: int = CreditCustomerRegularTequilaOrderRecordPaymentHistory.objects.filter(
            credit_customer_payment=instance.credit_customer_payment
        ).aggregate(total=Sum("amount_paid"))["total"]

        # obj3 = obj2.customer_dish
        if total == 0:
            obj2.payment_status = "unpaid"
        elif total >= obj2.get_total_amount_to_pay:
            obj2.payment_status = "paid"
        else:
            obj2.payment_status = "partial"

        obj2.save()
