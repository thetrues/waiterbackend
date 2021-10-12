import calendar
from typing import Dict

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bar.models import CustomerRegularTequilaOrderRecord, BarPayrol
from core.utils import get_date_objects


def get_today_response(response: Dict) -> str:
    today_date = timezone.localdate()
    response["today_date"] = today_date.__str__()

    return today_date


def structure_orders(qs, sales):
    sales["orders_structure"] = []
    for q in qs:
        temp_order_structure: Dict = {}
        temp_order_structure["order_id"] = q.id
        temp_order_structure["order_number"] = q.customer_orders_number
        temp_order_structure["payment_status"] = q.get_payment_status()
        temp_order_structure["payable_amount"] = q.get_total_price()
        temp_order_structure["paid_amount"] = q.get_paid_amount()
        temp_order_structure["remained_amount"] = q.get_remained_amount()
        temp_order_structure["orders_details"] = q.get_orders_detail

        sales["orders_structure"].append(temp_order_structure)

    return sales["orders_structure"]


def get_total_sales(qs):
    total_sales: int = 0
    for q in qs:
        total_sales += q.customerregulartequilaorderrecordpayment_set.aggregate(total=Sum("amount_paid"))["total"] or 0

    return total_sales


class DailyReport(APIView):
    """ Get daily reports """

    def get(self, request, *args, **kwargs):
        response: Dict = {}
        today_date = get_today_response(response)

        qs = self.get_queryset(today_date)

        sales: Dict = self.get_sales_response(qs)
        response["sales"] = sales

        return Response(response, status.HTTP_200_OK)

    def get_queryset(self, today_date):
        return (
            CustomerRegularTequilaOrderRecord.objects.filter(date_created__date=today_date)
                .select_related("regular_tequila_order_record", "created_by")
        )

    def get_sales_response(self, qs) -> Dict:
        sales: Dict = {}
        self.total_sales_and_orders(qs, sales)
        sales["orders_structure"] = structure_orders(qs, sales)
        # self.structure_orders(qs, sales)

        return sales

    def total_sales_and_orders(self, qs, sales):
        sales["total_sales"] = get_total_sales(qs)
        sales["total_orders"] = len(qs)


class MonthlyReport(APIView):
    """ Get Monthly Reports"""

    this_month = timezone.now()

    def get(self, request, *args, **kwargs):
        response: Dict = {}
        qs = self.get_queryset(self.this_month)
        self.get_current_month(response)

        sales: Dict = self.get_sales_response(qs)
        response["sales"] = sales

        expenses: Dict = self.get_expenses_response(response, self.this_month)
        response["expenses"] = expenses

        total_sales = response["sales"]["total_sales"]
        total_expenses = response["expenses"]["payrolls"]
        response["balance"] = total_sales - total_expenses

        return Response(response, status.HTTP_200_OK)

    def get_expenses_response(self, response: Dict, this_month) -> Dict:
        expenses: Dict = {}
        # monthly_payroll = self.get_monthly_payroll(this_month)
        expenses["payrolls"] = BarPayrol.objects.filter(
            date_paid__month=this_month.month, date_paid__year=this_month.year
        ).aggregate(total=Sum("amount_paid"))[
                                   "total"
                               ] or 0

        return expenses

    def get_monthly_payroll(self, this_month) -> Dict:
        monthly_payroll: Dict = {}
        qs = BarPayrol.objects.filter(
            date_paid__month=this_month.month, date_paid__year=this_month.year
        ).select_related("bar_payee")
        monthly_payroll["total_payment"] = qs.aggregate(total=Sum("amount_paid"))[
                                               "total"
                                           ] or 0
        monthly_payroll[
            "payments_structure"
        ] = BarPayrol.objects.get_monthly_payments(qs)

        return monthly_payroll

    def get_sales_response(self, qs) -> Dict:
        sales: Dict = {}
        self.total_sales_and_orders(qs, sales)
        sales["orders_structure"] = structure_orders(qs, sales)

        return sales

    def total_sales_and_orders(self, qs, sales):
        sales["total_sales"] = get_total_sales(qs)
        sales["total_orders"] = len(qs)

    def get_current_month(self, response: Dict) -> str:
        response["current_month"] = (
                calendar.month_name[self.this_month.month]
                + ", "
                + str(self.this_month.year)
        )

    def get_queryset(self, this_month):
        return (
            CustomerRegularTequilaOrderRecord.objects.filter(
                date_created__date__year=this_month.year,
                date_created__date__month=this_month.month,
            )
                .select_related("regular_tequila_order_record", "created_by")
        )


class CustomDateReport(APIView):
    """Get a custom date report"""

    def post(self, request, *args, **kwargs):
        response: Dict = {}
        first_date = request.data.get("first_date")
        second_date = request.data.get("second_date")

        try:
            date1, date2 = get_date_objects(first_date, second_date)
        except TypeError:
            return Response({"message": "Please choose dates range."})

        qs = self.get_queryset(date1, date2)

        self.get_custom_dates(response, date1, date2)

        sales: Dict = self.get_sales_response(qs)
        response["sales"] = sales

        expenses: Dict = self.get_expenses_response(response, date1, date2)
        response["expenses"] = expenses

        total_sales = response["sales"]["total_sales"]
        total_expenses = response["expenses"]["total_payrolls"]

        response["balance"] = total_sales - total_expenses

        return Response(response, status.HTTP_200_OK)

    def get_expenses_response(self, response: Dict, date1, date2) -> Dict:
        expenses: Dict = {}
        custom_payroll = self.get_custom_payrolls(date1, date2)
        expenses["total_payrolls"] = custom_payroll
        return expenses

    def get_custom_payrolls(self, date1, date2):
        return BarPayrol.objects.filter(date_paid__range=(date1, date2)).aggregate(total=Sum("amount_paid"))[
                   "total"] or 0

    def total_sales_and_orders(self, qs, sales):
        sales["total_sales"] = get_total_sales(qs)
        sales["total_orders"] = len(qs)

    def get_sales_response(self, qs) -> Dict:
        sales: Dict = {}
        self.total_sales_and_orders(qs, sales)
        sales["orders_structure"] = structure_orders(qs, sales)

        return sales

    def get_custom_dates(self, response: Dict, date1, date2):
        response["dates"] = "{} TO {}".format(str(date1), str(date2))

    def get_queryset(self, date1, date2):
        return (
            CustomerRegularTequilaOrderRecord.objects.filter(
                date_created__date__range=(date1, date2),
            )
                .select_related("regular_tequila_order_record", "created_by")
        )
