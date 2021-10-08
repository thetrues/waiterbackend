"""
This signal is for changing the item quantity inventory record.
"""
from bar.models import (
    CreditCustomerRegularTequilaOrderRecordPaymentHistory,
    RegularInventoryRecord,
    TekilaInventoryRecord,
    RegularOrderRecord,
)
from django.db.models.signals import post_save
from django.db.models.aggregates import Sum
from django.dispatch import receiver
from django.utils import timezone
from typing import NoReturn


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
