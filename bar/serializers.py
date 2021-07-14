from bar.models import RegularInventoryRecord, TekilaInventoryRecord
from rest_framework import serializers


class RegularInventoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularInventoryRecord
        exclude = ["date_perished"]


class TekilaInventoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TekilaInventoryRecord
        fields = "__all__"
