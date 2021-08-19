from user.models import User
from bar.models import (
    BarPayrol,
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
