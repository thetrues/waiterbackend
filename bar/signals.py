"""
This signal is for changing the item quantity inventory record.
"""
from typing import NoReturn
from bar.models import (
    CreditCustomerRegularOrderRecordPaymentHistory,
    RegularInventoryRecord,
    TekilaInventoryRecord,
    RegularOrderRecord,
)
from django.db.models.signals import post_save
from django.db.models.aggregates import Sum
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender=RegularOrderRecord)
def alter_regular_inventory_record(sender, instance, created, **kwargs) -> NoReturn:
    # sourcery skip: last-if-guard
    if created:
        regular_item_record = RegularInventoryRecord.objects.get(
            item=instance.item.item
        )
        regular_item_record.available_quantity -= int(instance.quantity)
        regular_item_record.save()
        if regular_item_record.available_quantity == 0:
            regular_item_record.stock_status = "unavailable"
            regular_item_record.date_perished = timezone.now()
            regular_item_record.save()


# @receiver(post_save, sender=CustomerRegularOrderRecord)
# def reduce_inv_item_for(sender, instance, created, **kwargs) -> NoReturn:
#     # sourcery skip: last-if-guard
#     if created:
#         perform_alter(instance)


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


@receiver(post_save, sender=CreditCustomerRegularOrderRecordPaymentHistory)
def update_payment_amounts(sender, instance, created, **kwargs) -> NoReturn:
    if created:
        obj = instance.credit_customer_payment
        obj.amount_paid = obj.amount_paid + instance.amount_paid
        obj.save()

        obj2 = instance.credit_customer_payment.record_order_payment_record
        obj2.amount_paid = obj2.amount_paid + instance.amount_paid
        obj2.date_updated = timezone.now()
        obj2.save()

        total = CreditCustomerRegularOrderRecordPaymentHistory.objects.filter(
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


# @receiver(post_save, sender=CreditCustomerTequilaOrderRecordPaymentHistory)
# def update_amounts_paid_for_tequila(sender, instance, created, **kwargs):
#     if created:
#         object = instance.credit_customer_payment
#         object.amount_paid = object.amount_paid + instance.amount_paid
#         object.save()

#         object2 = instance.credit_customer_payment.record_order_payment_record
#         object2.amount_paid = object2.amount_paid + instance.amount_paid
#         object2.date_updated = timezone.now()
#         object2.save()

#         total = CreditCustomerTequilaOrderRecordPaymentHistory.objects.filter(
#             credit_customer_payment=object
#         ).aggregate(total=Sum("amount_paid"))["total"]

#         if total == 0:
#             object2.payment_status = "unpaid"
#         elif total >= object2.get_total_amount_to_pay:
#             object2.payment_status = "paid"
#         else:
#             object2.payment_status = "partial"

#         object2.save()
