from bar.models import (
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
        Check if item quantity is not less than threshold.
        """
        if data["quantity"] <= data["threshold"]:
            raise serializers.ValidationError(
                "Item threshold must be less than quantity"
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
