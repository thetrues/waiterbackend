from typing import Dict, List

from rest_framework import status, viewsets, serializers
from rest_framework.response import Response

from core.models import CreditCustomer, Item, MeasurementUnit, Expenditure
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
            if serializer.validated_data.get("tequila"):
                tequila = True
            else:
                tequila = False
            Item.objects.create(
                name=serializer.validated_data.get("name"),
                unit=MeasurementUnit.objects.get(id=serializer.validated_data.get("unit")),
                item_for=serializer.validated_data.get("item_for"),
                tequila=tequila
            )
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


class ExpenditureView(viewsets.ModelViewSet):
    """  """

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Expenditure
            fields = "__all__"

    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=128)
        amount = serializers.IntegerField()
        expenditure_for = serializers.CharField(max_length=10)

    serializer_class = InputSerializer

    def get_queryset(self):
        return Expenditure.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        Expenditure.objects.create(**serializer.validated_data)

        return Response(status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        data = self.OutputSerializer(self.get_queryset(), many=True).data

        return Response(data=data, status=status.HTTP_200_OK)
