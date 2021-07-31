from restaurant.models import (
    Additive,
    CreditCustomerDishPaymentHistory,
    CustomerDish,
    CustomerDishPayment,
    Menu,
    RestaurantCustomerOrder,
    RestaurantPayrol,
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

    def validate_item(self, item):
        if item.item_for != "restaurant":
            raise serializers.ValidationError(
                f"Choose a restaurant item. {item.name} is for bar"
            )

        return item

    def to_representation(self, instance):
        rep = super(MainInventoryItemSerializer, self).to_representation(instance)
        rep["item"] = instance.item.name
        return rep


class MainInventoryItemRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainInventoryItemRecord
        fields = "__all__"


class MiscellaneousInventoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiscellaneousInventoryRecord
        fields = "__all__"

    def validate_item(self, item):
        if item.item_for != "restaurant":
            raise serializers.ValidationError(
                f"Choose a restaurant item. {item.name} is for bar"
            )

        return item

    def to_representation(self, instance):
        rep = super(MiscellaneousInventoryRecordSerializer, self).to_representation(instance)
        rep["item"] = instance.item.name
        return rep


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
        fields = ["customer_dish", "amount_paid", "payment_method"]


class CreditCustomerDishPaymentHistorySerializer(serializers.ModelSerializer):
    def validate_credit_customer_dish_payment(self, credit_customer_dish_payment):
        if (
            credit_customer_dish_payment.by_credit is False
            and credit_customer_dish_payment.payment_status == "paid"
        ):
            raise serializers.ValidationError(
                "This order was not taken by credit or is already paid."
            )

        return credit_customer_dish_payment

    class Meta:
        model = CreditCustomerDishPaymentHistory
        fields = "__all__"


class RestaurantPayrolSerializer(serializers.ModelSerializer):
    def validate_restaurant_payee(self, user):
        if user.user_type not in ["restaurant_waiter", "restaurant_cashier"]:
            raise serializers.ValidationError(
                f"{user.username} is a {user.get_user_type_display()}. Choose restaurant worker"
            )
        return user

    class Meta:
        model = RestaurantPayrol
        exclude = ["restaurant_payer"]

    def to_representation(self, instance):
        rep = super(RestaurantPayrolSerializer, self).to_representation(instance)
        rep["restaurant_payee"] = instance.restaurant_payee.username
        return rep
