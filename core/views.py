from core.models import CreditCustomer, Item, MeasurementUnit
from rest_framework.response import Response
from rest_framework import status, viewsets, serializers
from typing import Dict, List
from core.serializers import (
    CreditCustomerSerializer,
    MeasurementUnitSerializer,
    ItemSerializer,
)


class MeasurementUnitViewSet(viewsets.ModelViewSet):
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer


class ItemViewSet(viewsets.ModelViewSet):
    """ Item View API """

    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=128)
        unit = serializers.IntegerField()
        item_for = serializers.CharField(max_length=10)
        tequila = serializers.BooleanField()

    queryset = Item.objects.select_related("unit")
    serializer_class = ItemSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = Item(
                name=serializer.validated_data.get("name"),
                unit=MeasurementUnit.objects.get(id=serializer.validated_data.get("unit")),
                item_for=serializer.validated_data.get("item_for")
            )
            if serializer.validated_data.get("tequila"):
                item.tequila = True
            else:
                item.tequila = False
            item.save()
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return Response({"message": "Item Created"}, status=status.HTTP_201_CREATED)


class CreditCustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CreditCustomerSerializer

    def list(self, request, *args, **kwargs) -> Response:
        response: List[Dict] = []

        self.append_list(response)

        return Response(data=response, status=status.HTTP_200_OK)

    def append_list(self, response):
        for customer in self.get_queryset():
            temp_dict: Dict = {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "address": customer.address,
                "credit_limit": customer.credit_limit or 0,
                "today_balance": customer.get_today_balance(),
            }
            response.append(temp_dict)

    def get_queryset(self):
        return CreditCustomer.objects.all()
