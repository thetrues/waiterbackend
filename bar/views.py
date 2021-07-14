from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from bar.serializers import (
    RegularInventoryRecordSerializer,
    TekilaInventoryRecordSerializer,
)
from bar.models import RegularInventoryRecord, TekilaInventoryRecord
from rest_framework.authentication import TokenAuthentication


class RegularInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RegularInventoryRecord.objects.all()
    serializer_class = RegularInventoryRecordSerializer
    authentication_classes = [TokenAuthentication]

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = {
            "id": instance.id,
            "quantity": instance.quantity,
            "purchasing_price": float(instance.purchasing_price),
            "date_purchased": instance.date_purchased,
            "total_items": instance.total_items,
            "selling_price_per_item": instance.selling_price_per_item,
            "estimated_total_cash_after_sale": float(instance.estimate_sales()),
            "estimated_profit_after_sale": float(instance.estimate_profit()),
            "item": instance.item.name,
            "measurement_unit": instance.item.unit.name,
        }

        return Response(data=response, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        response: list = []
        for record in self.queryset:
            response.append(
                {
                    "id": record.id,
                    "quantity": record.quantity,
                    "purchasing_price": float(record.purchasing_price),
                    "date_purchased": record.date_purchased,
                    "total_items": record.total_items,
                    "selling_price_per_item": record.selling_price_per_item,
                    "estimated_total_cash_after_sale": float(record.estimate_sales()),
                    "estimated_profit_after_sale": float(record.estimate_profit()),
                    "item": record.item.name,
                    "measurement_unit": record.item.unit.name,
                }
            )
        return Response(data=response, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_total_cash_after_sale(self, request, pk=None):
        return Response(
            {
                "estimated_total_cash_after_sale": float(
                    self.get_object().estimate_sales()
                )
            },
            status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_profit_after_sale(self, request, pk=None):
        return Response(
            {"estimated_profit_after_sale": float(self.get_object().estimate_profit())},
            status.HTTP_200_OK,
        )


class TekilaInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = TekilaInventoryRecord.objects.all()
    serializer_class = TekilaInventoryRecordSerializer
    authentication_classes = [TokenAuthentication]

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_total_cash_after_sale(self, request, pk=None):
        return Response(
            {"estimated_total_cash_after_sale": self.get_object().estimate_sales()},
            status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_profit_after_sale(self, request, pk=None):
        return Response(
            {"estimated_profit_after_sale": self.get_object().estimate_profit()},
            status.HTTP_200_OK,
        )
