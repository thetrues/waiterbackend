from user.models import User
from django.db.models import query
from rest_framework import serializers
from core.models import Additive, Item, InventoryRecord, Menu


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "unit"]


class MenuSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Menu
        fields = ["id", "name", "price", "image"]


class AdditiveSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Additive
        fields = ["id", "name"]


class InventoryRecordSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InventoryRecord
        fields = [
            "item",
            "quantity",
            "price",
            "threshold",
            "created_at",
            "updated_at",
            "created_by",
        ]
