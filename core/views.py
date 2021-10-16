from core.models import CreditCustomer, Item, MeasurementUnit
from rest_framework.response import Response
from rest_framework import status, viewsets
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
    # authentication_classes = []
    # permission_classes = []
    queryset = Item.objects.select_related("unit")
    serializer_class = ItemSerializer


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
