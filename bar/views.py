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
