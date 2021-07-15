from bar.models import RegularInventoryRecord, TekilaInventoryRecord
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
