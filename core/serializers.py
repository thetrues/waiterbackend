from core.models import CreditCustomer, Item, MeasurementUnit
from rest_framework import serializers


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "unit", "item_for"]

    def to_representation(self, instance):
        rep = super(ItemSerializer, self).to_representation(instance)
        rep["unit"] = instance.unit.name
        rep["item_for"] = instance.item_for.title()
        return rep


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name"]


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = "__all__"


class CreditCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCustomer
        fields = "__all__"
    
    def to_representation(self, instance):
        rep = super(CreditCustomerSerializer, self).to_representation(instance)
        credit_limit = instance.credit_limit
        rep["credit_limit"] = credit_limit or 0.0
        return rep
