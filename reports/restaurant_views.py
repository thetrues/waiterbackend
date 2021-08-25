from restaurant.models import CustomerDishPayment, MiscellaneousInventoryRecord
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
            CustomerDishPayment.objects.filter(date_paid__date__lt=todays_date)
            .select_related("customer_dish")
            .prefetch_related("customer_dish__orders")
        )

        response["todays_date"] = todays_date.__str__()
        sales: Dict = {}
        sales["total_sales"] = qs.aggregate(total=Sum("amount_paid"))["total"]
        sales["total_dishes"] = len(qs)
        sales["dishes_structure"] = []
        for q in qs:
            temp_dish_structure: Dict = {}
            temp_dish_structure["dish_id"] = q.id
            temp_dish_structure["dish_number"] = q.customer_dish.dish_number
            temp_dish_structure["payment_status"] = q.payment_status
            temp_dish_structure["by_credit"] = q.by_credit
            temp_dish_structure["payable_amount"] = q.get_total_amount_to_pay
            temp_dish_structure["paid_amount"] = q.amount_paid
            temp_dish_structure["remained_amount"] = q.get_remaining_amount
            temp_dish_structure["dish_detail"] = q.customer_dish.get_dish_detail

            sales["dishes_structure"].append(temp_dish_structure)

    def total_sales_and_dishes(self, qs, sales):
        sales["total_sales"] = qs.aggregate(total=Sum("amount_paid"))["total"]
        sales["total_dishes"] = len(qs)
