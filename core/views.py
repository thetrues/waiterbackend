from typing import Dict, List
from django.db.models.aggregates import Sum
from django.utils import timezone
from rest_framework.response import Response
from core.models import CreditCustomer, Item, MeasurementUnit
from rest_framework import status, viewsets
from core.serializers import (
    CreditCustomerSerializer,
    MeasurementUnitSerializer,
    ItemSerializer,
)


class MeasurementUnitViewSet(viewsets.ModelViewSet):
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.select_related("unit")
    serializer_class = ItemSerializer


class CreditCustomerViewSet(viewsets.ModelViewSet):
    queryset = CreditCustomer.objects.all()
    serializer_class = CreditCustomerSerializer

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []

        self.append_list(response)

        return Response(data=response, status=status.HTTP_200_OK)

    def append_list(self, response):
        for customer in self.queryset:
            today_spend = customer.creditcustomerdishpayment_set.filter(
                date_created=timezone.localdate()
            ).aggregate(total=Sum("amount_paid"))["total"]
            if not today_spend:
                today_spend = 0.0
            temp_dict: Dict = {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "address": customer.address,
                "credit_limit": customer.credit_limit,
                "today_balance": customer.credit_limit - today_spend,
            }
            response.append(temp_dict)
