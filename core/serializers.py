from rest_framework import serializers
from core.models import Additive, Item, Menu


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "unit"]


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ["id", "name", "price"]


class AdditiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Additive
        fields = ["id", "name"]
