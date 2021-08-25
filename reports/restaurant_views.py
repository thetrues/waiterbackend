from restaurant.models import CustomerDishPayment
from rest_framework.response import Response
from django.db.models.aggregates import Sum
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from typing import Dict


class DailyReport(APIView):
    """Get Daily Reports"""

    permission_classes = []
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        response: Dict = {}
        todays_date = timezone.localdate()

        qs = (
            CustomerDishPayment.objects.filter(date_paid__date=todays_date)
            .select_related("customer_dish")
            .prefetch_related("customer_dish__orders")
        )

        response["todays_date"] = todays_date.__str__()
        sales: Dict = {}
        sales["total_sales"] = qs.aggregate(total=Sum("amount_paid"))["total"]
        response["sales"] = sales

        return Response(response, status.HTTP_200_OK)
