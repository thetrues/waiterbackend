from rest_framework.response import Response
from django.db.models.aggregates import Sum
from rest_framework.views import APIView
from restaurant.models import (
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
    CustomerDishPayment,
    RestaurantPayrol,
)
from reports.base import BaseReport
from rest_framework import status
from django.utils import timezone
from typing import Dict, List
import calendar


class DailyReport(BaseReport, APIView):
    """Get Daily Reports"""

    def get(self, request, *args, **kwargs):
        response: Dict = {}
        todays_date = self.get_todays_response(response)

        qs = self.get_queryset(todays_date)

        sales: Dict = self.get_sales_response(qs)
        response["sales"] = sales

        expenses: Dict = self.get_expenses_response(response, todays_date)
        response["expenses"] = expenses

        total_sales = response["sales"]["total_sales"]
        total_expenses = response["expenses"]["total_expense"]

        response["balance"] = total_sales - total_expenses

        return Response(response, status.HTTP_200_OK)

    def get_expenses_response(self, response: Dict, todays_date) -> Dict:
        expenses: Dict = {}
        total_misc_expense, misc_qs = self.get_total_misc_expense_and_misc_qs(
            todays_date
        )
        total_main_expense, gabbage = self.get_total_main_expense_and_main_qs(
            todays_date
        )
        misc_inventory = self.assign_total_expense(
            expenses, total_misc_expense, total_main_expense
        )

        misc_inventory["total_miscellenous_purchases"] = total_misc_expense

        expenses["misc_inventory"] = misc_inventory
        temp_miscellenous_items = self.append_misc_items(misc_qs)
        misc_inventory["miscellenous_items"] = temp_miscellenous_items

        main_inventory: Dict = {}
        (
            main_inventory["total_consuption_estimation"],
            main_qs,
        ) = self.get_total_main_expense_and_main_qs(todays_date)
        temp_issued_items = self.append_temp_issued_items(main_qs)

        main_inventory["issued_items"] = temp_issued_items

        expenses["main_inventory"] = main_inventory

        return expenses

    def assign_total_expense(self, expenses, total_misc_expense, total_main_expense):
        expenses["total_expense"] = total_misc_expense + total_main_expense
        misc_inventory: Dict = {}

        return misc_inventory

    def get_todays_response(self, response: Dict) -> str:
        todays_date = timezone.localdate()
        response["todays_date"] = todays_date.__str__()

        return todays_date

    def get_total_main_expense_and_main_qs(self, todays_date):
        main_qs = MainInventoryItemRecordStockOut.objects.filter(
            date_out=todays_date
        ).select_related("item_record")
        total_main_expense: float = self.get_total_main_expense(main_qs)
        # total_main_expense: float = main_qs.aggregate(total=Sum("get_ppu"))["total"]

        return total_main_expense, main_qs

    def get_total_misc_expense_and_misc_qs(self, todays_date):
        misc_qs = MiscellaneousInventoryRecord.objects.filter(
            date_purchased=todays_date
        ).select_related("item", "item__unit")
        total_misc_expense: float = misc_qs.aggregate(total=Sum("purchasing_price"))[
            "total"
        ]

        return total_misc_expense, misc_qs

    def get_queryset(self, todays_date):
        return (
            CustomerDishPayment.objects.filter(date_paid__date=todays_date)
            .select_related("customer_dish")
            .prefetch_related("customer_dish__orders")
        )


class MonthlyReport(BaseReport, APIView):
    """Get a monthly report"""

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
        total_expenses = response["expenses"]["total_expense"]

        response["balance"] = total_sales - total_expenses

        return Response(response, status.HTTP_200_OK)

    def get_current_month(self, response: Dict) -> str:
        response["current_month"] = (
            calendar.month_name[self.this_month.month]
            + ", "
            + str(self.this_month.year)
        )

    def get_expenses_response(self, response: Dict, this_month) -> Dict:
        expenses: Dict = {}
        total_misc_expense, misc_qs = self.get_total_misc_expense_and_misc_qs(
            this_month
        )
        total_main_expense, gabbage = self.get_total_main_expense_and_main_qs(
            this_month
        )
        total_payrol = self.get_total(this_month)
        misc_inventory = self.assign_total_expense(
            expenses, total_misc_expense, total_main_expense, total_payrol
        )

        misc_inventory["total_miscellenous_purchases"] = total_misc_expense

        expenses["misc_inventory"] = misc_inventory
        temp_miscellenous_items = self.append_misc_items(misc_qs)
        misc_inventory["miscellenous_items"] = temp_miscellenous_items

        main_inventory: Dict = {}
        (
            main_inventory["total_consuption_estimation"],
            main_qs,
        ) = self.get_total_main_expense_and_main_qs(this_month)
        temp_issued_items = self.append_temp_issued_items(main_qs)

        main_inventory["issued_items"] = temp_issued_items

        expenses["main_inventory"] = main_inventory

        # Payrols
        monthly_payrol = self.get_monthly_payrol(this_month)

        expenses["payrols"] = monthly_payrol

        return expenses

    def get_total(self, this_month):
        return RestaurantPayrol.objects.filter(
            date_paid__month=this_month.month, date_paid__year=this_month.year
        ).aggregate(total=Sum("amount_paid"))["total"]

    def get_monthly_payrol(self, this_month) -> Dict:
        monthly_payrol: Dict = {}
        qs = RestaurantPayrol.objects.filter(
            date_paid__month=this_month.month, date_paid__year=this_month.year
        ).select_related("restaurant_payee")
        monthly_payrol["total_payment"] = qs.aggregate(total=Sum("amount_paid"))[
            "total"
        ]
        monthly_payrol[
            "payments_structure"
        ] = RestaurantPayrol.objects.get_monthly_payments(qs)

        return monthly_payrol

    def assign_total_expense(
        self, expenses, total_misc_expense, total_main_expense, total_payrol
    ):
        expenses["total_expense"] = (
            total_misc_expense + total_main_expense + total_payrol
        )
        misc_inventory: Dict = {}

        return misc_inventory

    def get_total_main_expense_and_main_qs(self, this_month):
        main_qs = MainInventoryItemRecordStockOut.objects.filter(
            date_out__month=this_month.month, date_out__year=this_month.year
        ).select_related("item_record")
        total_main_expense: float = self.get_total_main_expense(main_qs)
        # total_main_expense: float = main_qs.aggregate(total=Sum("get_ppu"))["total"]

        return total_main_expense, main_qs

    def get_total_misc_expense_and_misc_qs(self, this_month):
        misc_qs = MiscellaneousInventoryRecord.objects.filter(
            date_purchased__year=this_month.year,
            date_purchased__month=this_month.month,
        ).select_related("item", "item__unit")
        total_misc_expense: float = misc_qs.aggregate(total=Sum("purchasing_price"))[
            "total"
        ]

        return total_misc_expense or 0, misc_qs

    def get_queryset(self, this_month):
        return (
            CustomerDishPayment.objects.filter(
                date_paid__date__year=this_month.year,
                date_paid__date__month=this_month.month,
            )
            .select_related("customer_dish")
            .prefetch_related("customer_dish__orders")
        )


class CustomerDateReport(APIView):
    """Get a custom date report"""

    # def get(self, request, *args, **kwargs):
    #     response: Dict = {}
    #     todays_date = self.get_monthly_response(response)

    # def get_monthly_response(response):
    #     todays_date = timezone.localdate()
    #     response["todays_date"] = todays_date.__str__()

    #     return todays_date
