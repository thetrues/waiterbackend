from core.models import CreditCustomer, Item, MeasurementUnit
from rest_framework import viewsets
from core.serializers import (
    CreditCustomerSerializer,
    MeasurementUnitSerializer,
    ItemSerializer,
)
from icecream import ic


class MeasurementUnitViewSet(viewsets.ModelViewSet):
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class CreditCustomerViewSet(viewsets.ModelViewSet):
    queryset = CreditCustomer.objects.all()
    serializer_class = CreditCustomerSerializer
