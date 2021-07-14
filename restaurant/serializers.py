from restaurant.models import (
    Additive,
    CustomerDish,
    CustomerDishPayment,
    Menu,
    RestaurantCustomerOrder,
)
from restaurant.models import (
    MainInventoryItem,
    MainInventoryItemRecord,
    MiscellaneousInventoryRecord,
)
from rest_framework import serializers


class MainInventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainInventoryItem
        fields = "__all__"


class MainInventoryItemRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainInventoryItemRecord
        fields = "__all__"


class MiscellaneousInventoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiscellaneousInventoryRecord
        fields = "__all__"


class MenuSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Menu
        fields = ["id", "name", "description", "price", "image"]


class AdditiveSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Additive
        fields = ["id", "name"]


class RestaurantCustomerOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantCustomerOrder
        fields = [
            "sub_menu",
            "quantity",
        ]


class CustomerDishSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDish
        fields = [
            "customer_name",
            "customer_phone",
        ]


class CustomerDishPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDishPayment
        fields = "__all__"
