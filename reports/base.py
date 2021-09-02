from typing import Dict, List

from django.db.models.aggregates import Sum


class BaseReporter(object):
    """"""

    def append_misc_items(self, misc_qs) -> List:
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

        return temp_miscellenous_items

    def append_temp_issued_items(self, main_qs) -> List:
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

        return temp_issued_items

    def get_sales_response(self, qs) -> Dict:
        sales: Dict = {}
        self.total_sales_and_dishes(qs, sales)
        self.structure_dishes(qs, sales)

        return sales

    def get_total_main_expense(self, main_qs) -> float:
        total_main_expense: float = 0.0
        for qs in main_qs:
            total_main_expense += qs.get_ppu()

        return total_main_expense

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
