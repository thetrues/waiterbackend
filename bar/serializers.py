from django.db.models.aggregates import Sum
from django.utils import timezone
from user.models import User
from bar.models import (
    BarPayrol,
    CreditCustomerRegularOrderRecordPaymentHistory,
    CreditCustomerTequilaOrderRecordPaymentHistory,
    CustomerRegularOrderRecord,
    CustomerRegularOrderRecordPayment,
    CustomerTequilaOrderRecord,
    CustomerTequilaOrderRecordPayment,
    RegularOrderRecord,
    RegularInventoryRecord,
    TekilaInventoryRecord,
    TequilaOrderRecord,
)
from rest_framework import serializers


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
        exclude = ["date_perished", "available_quantity"]


class TekilaInventoryRecordSerializer(serializers.ModelSerializer):
    def validate(self, data):
        """
        Check if item quantity is not less than threshold.
        """
        if data["quantity"] <= data["threshold"]:
            raise serializers.ValidationError(
                "Item threshold must be less than quantity"
            )
        return data

    class Meta:
        model = TekilaInventoryRecord
        exclude = ["date_perished", "available_quantity"]


class OrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularOrderRecord
        exclude = ["order_number", "created_by", "date_created"]


class CustomerOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRegularOrderRecord
        fields = ["customer_name", "customer_phone"]


class CustomerOrderRecordPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRegularOrderRecordPayment
        exclude = ["payment_status", "date_paid", "date_updated", "created_by"]


class BarPayrolSerializer(serializers.ModelSerializer):
    def validate_bar_payee(self, user):
        if user.user_type not in ["bar_waiter", "bar_cashier"]:
            raise serializers.ValidationError(
                f"{user.username} is a {user.get_user_type_display()}. Choose bar worker"
            )
        return user

    class Meta:
        model = BarPayrol
        exclude = ["bar_payer"]

    def to_representation(self, instance):
        rep = super(BarPayrolSerializer, self).to_representation(instance)
        rep["bar_payee"] = instance.bar_payee.username
        return rep


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


class TequilaOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TequilaOrderRecord
        exclude = ["order_number", "created_by", "date_created"]


class TequilaCustomerOrderRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTequilaOrderRecord
        fields = ["customer_name", "customer_phone"]


class TequilaCustomerOrderRecordPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTequilaOrderRecordPayment
        exclude = ["payment_status", "date_paid", "date_updated", "created_by"]


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
