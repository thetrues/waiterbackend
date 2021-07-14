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
        response: dict = self.get_res(instance)

        return Response(data=response, status=status.HTTP_200_OK)

    def get_res(self, instance):
        return {
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

    def list(self, request, *args, **kwargs):
        response: list = []
        for record in self.queryset:
            response.append(self.get_res(record))
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

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = self.get_res(instance)

        return Response(data=response, status=status.HTTP_200_OK)

    def get_res(self, instance) -> dict():
        return {
            "id": instance.id,
            "quantity": instance.quantity,
            "purchasing_price": float(instance.purchasing_price),
            "date_purchased": instance.date_purchased,
            "date_perished": instance.date_perished,
            "total_shots_per_tekila": instance.total_shots_per_tekila,
            "selling_price_per_shot": instance.selling_price_per_shot,
            "estimated_total_cash_after_sale": float(instance.estimate_sales()),
            "estimated_profit_after_sale": float(instance.estimate_profit()),
            "item": instance.item.name,
            "measurement_unit": instance.item.unit.name,
        }

    def list(self, request, *args, **kwargs):
        response: list = []
        for record in self.queryset:
            response.append(self.get_res(record))
        return Response(data=response, status=status.HTTP_200_OK)

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


# Sales Management

