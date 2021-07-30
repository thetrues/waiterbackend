from core.models import CreditCustomer, Item, MeasurementUnit
from rest_framework import serializers


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "unit"]

    def to_representation(self, instance):
        rep = super(ItemSerializer, self).to_representation(instance)
        rep["unit"] = instance.unit.name
        return rep


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = "__all__"


class CreditCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCustomer
        fields = "__all__"
