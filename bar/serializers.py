from user.models import User
from bar.models import (
    BarPayrol,
    CustomerRegularOrderRecord,
    CustomerRegularOrderRecordPayment,
    RegularOrderRecord,
    RegularInventoryRecord,
    TekilaInventoryRecord,
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

    bar_payee = serializers.ChoiceField(
        User.objects.filter(user_type__in=["bar_waiter", "bar_cashier"])
    )

    class Meta:
        model = BarPayrol
        exclude = ["bar_payer", "date_paid"]
