from django.db.models.aggregates import Sum
from bar.models import (
    CreditCustomerRegularTequilaOrderRecordPaymentHistory,
    CreditCustomerRegularOrderRecordPaymentHistory,
    CreditCustomerTequilaOrderRecordPaymentHistory,
    CustomerRegularTequilaOrderRecordPayment,
    CustomerRegularOrderRecordPayment,
    CustomerRegularTequilaOrderRecord,
    CustomerTequilaOrderRecordPayment,
    CustomerRegularOrderRecord,
    CustomerTequilaOrderRecord,
    RegularTequilaOrderRecord,
    RegularInventoryRecord,
    TekilaInventoryRecord,
    RegularOrderRecord,
    TequilaOrderRecord,
    BarPayrol,
)
from rest_framework import serializers
from django.utils import timezone
from typing import List 


class RegularInventoryRecordSerializer(serializers.ModelSerializer):
    def validate(self, data):
        """
        Check if item total_items is not less than threshold.
        """
        if data["total_items"] <= data["threshold"]:
            raise serializers.ValidationError(
                "Item threshold must be less than total items"
            )
        return data

    class Meta:
        model = RegularInventoryRecord
        exclude: List[str] = ["date_perished", "available_quantity"]


class TekilaInventoryRecordSerializer(serializers.ModelSerializer):
    def validate(self, data):
        """
        Check if item quantity is not less than threshold.
        """
        if data["total_shots_per_tekila"] <= data["threshold"]:
            raise serializers.ValidationError(
                "Item threshold must be less than quantity"
            )
        return data

    class Meta:
        model = TekilaInventoryRecord
        exclude: List[str] = ["date_perished", "available_quantity"]


class OrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularOrderRecord
        exclude: List[str] = ["order_number", "created_by", "date_created"]


class RegularTequilaOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularTequilaOrderRecord
        exclude: List[str] = [
            "order_number",
            "created_by",
            "date_created",
            "regular_items",
            "tequila_items",
        ]


class CustomerOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRegularOrderRecord
        fields: List[str] = ["customer_name", "customer_phone"]


class CustomerRegularTequilaOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRegularTequilaOrderRecord
        fields: List[str] = ["customer_name", "customer_phone"]


class CustomerOrderRecordPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRegularOrderRecordPayment
        exclude: List[str] = ["payment_status", "date_paid", "date_updated", "created_by"]


class CustomerRegularTequilaOrderRecordPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRegularTequilaOrderRecordPayment
        exclude: List[str] = [
            "payment_status",
            "date_paid",
            "date_updated",
            "created_by",
            "customer_regular_tequila_order_record",
        ]


class BarPayrolSerializer(serializers.ModelSerializer):
    # def validate_bar_payee(self, user):
    #     if user.user_type not in ["bar_waiter", "bar_cashier"]:
    #         raise serializers.ValidationError(
    #             f"{user.username} is a {user.get_user_type_display()}. Choose bar worker"
    #         )
    #     return user

    class Meta:
        model = BarPayrol
        # fields = "__all__"
        exclude = ["bar_payer"]

    # def to_representation(self, instance):
    #     rep = super(BarPayrolSerializer, self).to_representation(instance)
    #     rep["bar_payee"] = instance.bar_payee.username
    #     return rep


class CreditCustomerRegularOrderRecordPaymentHistorySerializer(
    serializers.ModelSerializer
):
    def validate_credit_customer_payment(self, credit_customer_payment):
        if (
            credit_customer_payment.record_order_payment_record.by_credit is False
            and credit_customer_payment.record_order_payment_record.payment_status
            == "paid"
        ):
            raise serializers.ValidationError(
                "This order was not taken by credit or is already paid."
            )

        return credit_customer_payment

    class Meta:
        model = CreditCustomerRegularOrderRecordPaymentHistory
        fields = "__all__"


class CreditCustomerRegularTequilaOrderRecordPaymentHistorySerializer(
    serializers.ModelSerializer
):
    def validate_credit_customer_payment(self, credit_customer_payment):
        if (
            credit_customer_payment.record_order_payment_record.by_credit is False
            and credit_customer_payment.record_order_payment_record.payment_status
            == "paid"
        ):
            raise serializers.ValidationError(
                "This order was not taken by credit or is already paid."
            )

        return credit_customer_payment

    class Meta:
        model = CreditCustomerRegularTequilaOrderRecordPaymentHistory
        fields = "__all__"


class TequilaOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TequilaOrderRecord
        exclude: List[str] = ["order_number", "created_by", "date_created"]


class TequilaCustomerOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTequilaOrderRecord
        fields: List[str] = ["customer_name", "customer_phone"]


class TequilaCustomerOrderRecordPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTequilaOrderRecordPayment
        exclude: List[str] = ["payment_status", "date_paid", "date_updated", "created_by"]


class CreditCustomerTequilaOrderRecordPaymentHistorySerializer(
    serializers.ModelSerializer
):
    def validate_credit_customer_payment(self, credit_customer_payment):
        if (
            credit_customer_payment.record_order_payment_record.by_credit is False
            and credit_customer_payment.record_order_payment_record.payment_status
            == "paid"
        ):
            raise serializers.ValidationError(
                "This order was not taken by credit or is already paid."
            )

        return credit_customer_payment

    def create(self, validated_data):
        payment_history = CreditCustomerTequilaOrderRecordPaymentHistory.objects.create(
            **validated_data,
        )

        object = self.increment_amount_paid_for_ccp(
            payment_history
        )  # ccp: credit_customer_payment

        object2 = self.increment_amount_paid_for_ropr(
            payment_history
        )  # ropr: record_order_payment_record

        total = self.get_total_amount_paid(object)

        self.change_payment_status(object2, total)

        return payment_history

    def increment_amount_paid_for_ropr(self, payment_history):
        object2 = payment_history.credit_customer_payment.record_order_payment_record
        object2.amount_paid = object2.amount_paid + payment_history.amount_paid
        object2.date_updated = timezone.now()
        object2.save()
        object2.change_payment_status()
        return object2

    def increment_amount_paid_for_ccp(self, payment_history):
        object = payment_history.credit_customer_payment
        if object.amount_paid:
            object.amount_paid = object.amount_paid + payment_history.amount_paid
        else:
            object.amount_paid = payment_history.amount_paid
        object.save()
        return object

    def get_total_amount_paid(self, object):
        return CreditCustomerTequilaOrderRecordPaymentHistory.objects.filter(
            credit_customer_payment=object
        ).aggregate(total=Sum("amount_paid"))["total"]

    def change_payment_status(self, object2, total):
        if total == 0:
            object2.payment_status = "unpaid"
        elif total >= object2.get_total_amount_to_pay:
            object2.payment_status = "paid"
        else:
            object2.payment_status = "partial"

        object2.save()

    class Meta:
        model = CreditCustomerTequilaOrderRecordPaymentHistory
        fields = "__all__"
