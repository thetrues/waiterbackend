from restaurant.models import (
    CustomerDishPayment,
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
)
from rest_framework.response import Response
from django.db.models.aggregates import Sum
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from typing import Dict, List


class DailyReport(APIView):
    """Get Daily Reports"""

    permission_classes = []
    authentication_classes = []

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

    def get_expenses_response(self, response, todays_date):
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
        temp_miscellenous_items: List = []
        for misc_item in misc_qs:
            temp_miscellenous_items.append(
                {
                    "item_id": misc_item.id,
                    "item_name": misc_item.item.name,
                    "purchased_quantity": "{} {}".format(
                        misc_item.quantity, misc_item.item.unit.name
                    ),
                    "purchasing_price": "{} TZS".format(misc_item.purchasing_price),
                },
            )
        misc_inventory["miscellenous_items"] = temp_miscellenous_items

        main_inventory: Dict = {}
        (
            main_inventory["total_consuption_estimation"],
            main_qs,
        ) = self.get_total_main_expense_and_main_qs(todays_date)
        temp_issued_items: List = []
        for qs in main_qs:
            temp_issued_items.append(
                {
                    "item_id": qs.id,
                    "item_name": qs.item_record.main_inventory_item.item.name,
                    "issued_quantity": "{} {}".format(
                        qs.quantity_out,
                        qs.item_record.main_inventory_item.item.unit.name,
                    ),
                    "estimated_price": qs.item_record.ppu,
                },
            )

        main_inventory["issued_items"] = temp_issued_items

        expenses["main_inventory"] = main_inventory

        return expenses

    def assign_total_expense(self, expenses, total_misc_expense, total_main_expense):
        expenses["total_expense"] = total_misc_expense + total_main_expense
        misc_inventory: Dict = {}
        return misc_inventory

    def get_todays_response(self, response):
        todays_date = timezone.localdate()
        response["todays_date"] = todays_date.__str__()
        return todays_date

    def get_sales_response(self, qs) -> Dict:
        sales: Dict = {}
        self.total_sales_and_dishes(qs, sales)
        self.structure_dishes(qs, sales)

        return sales

    def get_total_main_expense_and_main_qs(self, todays_date):
        main_qs = MainInventoryItemRecordStockOut.objects.filter(
            date_out__lt=todays_date
        ).select_related("item_record")
        total_main_expense: float = self.get_total_main_expense(main_qs)

        # total_main_expense: float = main_qs.aggregate(total=Sum("get_ppu"))["total"]

        return total_main_expense, main_qs

    def get_total_main_expense(self, main_qs) -> float:
        total_main_expense: float = 00
        for qs in main_qs:
            total_main_expense += qs.get_ppu()
        return total_main_expense

    def get_total_misc_expense_and_misc_qs(self, todays_date):
        misc_qs = MiscellaneousInventoryRecord.objects.filter(
            date_purchased__lt=todays_date
        ).select_related("item", "item__unit")
        total_misc_expense = misc_qs.aggregate(total=Sum("purchasing_price"))["total"]

        return total_misc_expense, misc_qs

    def get_queryset(self, todays_date):
        return (
            CustomerDishPayment.objects.filter(
                date_paid__date__lt=todays_date
            )  # remove __lt
            .select_related("customer_dish")
            .prefetch_related("customer_dish__orders")
        )

    def structure_dishes(self, qs, sales):
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
