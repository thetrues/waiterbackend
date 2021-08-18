from django.db.models.aggregates import Sum
from django.db.models.manager import Manager
from django.db.models import F
from user.models import User
from django.db import models
from core.models import (
    BaseCreditCustomerPayment,
    BaseCustomerOrderRecord,
    BaseInventory,
    BaseOrderRecord,
    BasePayment,
    BasePayrol,
    Item,
)
from typing import List

# Inventory Management


class RegularInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_items = models.IntegerField()
    selling_price_per_item = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self) -> str():
        return str(self.item)

    def estimate_sales(self):
        return self.selling_price_per_item * self.total_items

    def estimate_profit(self):
        return self.estimate_sales() - self.purchasing_price

    def get_orders_history(self) -> dict():
        orders_history: dict = {}
        qs = self.regularorderrecord_set.select_related("created_by")
        self._get_total_ordered_items(orders_history, qs)
        self._get_total_income(orders_history, qs)
        self._get_orders_structure(orders_history, qs)

        return orders_history

    def _get_orders_structure(self, orders_history, qs):
        orders_structure: dict = {}
        for ord in qs:
            splited_date = str(ord.date_created).split(" ")
            orders_structure["order_id"] = ord.id
            orders_structure["order_number"] = ord.order_number
            orders_structure["quantity"] = ord.quantity
            orders_structure["total_price"] = ord.total
            orders_structure["date"] = splited_date[0]
            orders_structure["time"] = splited_date[1].split(".")[0]
            orders_structure["created_by"] = ord.created_by.username

        orders_history["orders_structure"] = orders_structure

    def _get_total_income(self, orders_history, qs):
        orders_history["total_income"] = qs.annotate(
            multiple=F("item__selling_price_per_item") * F("item__quantity")
        ).aggregate(Sum("multiple"))["multiple__sum"]

    def _get_total_ordered_items(self, orders_history, qs):
        orders_history["total_ordered_items"] = qs.aggregate(quantity=Sum("quantity"))[
            "quantity"
        ]

    class Meta:
        ordering: List = ["-id"]
        verbose_name: str = "Regular Inventory Record"
        verbose_name_plural: str = "Regular Inventory Records"


class TekilaInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_shots_per_tekila = models.IntegerField()
    selling_price_per_shot = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self):
        return self.item.name

    def estimate_sales(self) -> float():
        return self.selling_price_per_shot * self.total_shots_per_tekila * self.quantity

    def estimate_profit(self) -> float():
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: list = ["-id"]
        verbose_name: str = "Tequila Inventory Record"
        verbose_name_plural: str = "Tequila Inventory Records"


# Sale Management


class TequilaOrderRecord(BaseOrderRecord):
    item = models.ForeignKey(TekilaInventoryRecord, on_delete=models.CASCADE)

    def __str__(self) -> str():
        return self.item.item.name

    @property
    def total(self):
        return float(self.item.total_shots_per_tekila * self.quantity)

    class Meta:
        verbose_name: str = "Tequila Order Record"
        verbose_name_plural: str = "Tequila Order Records"


class CustomerTequilaOrderRecord(BaseCustomerOrderRecord):
    orders = models.ManyToManyField(TequilaOrderRecord)

    @property
    def get_total_price(self) -> float():
        """f(n) = n . Linear Function"""
        res_: int = 0
        for order in self.orders.all():
            res_ += order.total
        return res_

    @property
    def get_orders_detail(self):
        """f(n) = n . Linear Function"""
        res: list = []
        [
            res.append(
                {
                    "order_id": order.id,
                    "item_name": order.item.item.name,
                    "ordered_quantity": order.quantity,
                    "price_per_shot": float(order.item.selling_price_per_shot),
                    "order_total_price": order.total,
                    "order_number": order.order_number,
                    "created_by": order.created_by.username,
                    "date_created": order.date_created,
                },
            )
            for order in self.orders.all()
        ]
        return res

    class Meta:
        verbose_name = "Customer Regular Order Record"
        verbose_name_plural = "Customer Regular Order Records"


class CustomerTequilaOrderRecordPayment(BasePayment):
    customer_order_record = models.ForeignKey(
        CustomerTequilaOrderRecord, on_delete=models.CASCADE
    )

    def __str__(self) -> str():
        """f(n) = c; c=1 Constant Function"""
        return "{}: Payment Status: {}".format(
            self.customer_order_record, self.payment_status.title()
        )

    @property
    def get_total_amount_to_pay(self):
        return float(self.customer_order_record.get_total_price)

    @property
    def get_remaining_amount(self):
        return float(self.get_total_amount_to_pay - self.amount_paid)

    class Meta:
        verbose_name: str = "Customer Tequila Order Record Payment"
        verbose_name_plural: str = "Customer Tequila Order Record Payments"


class RegularOrderRecord(BaseOrderRecord):
    item = models.ForeignKey(RegularInventoryRecord, on_delete=models.CASCADE)

    def __str__(self) -> str():
        return self.item.item.name

    @property
    def total(self):
        return float(self.item.selling_price_per_item * self.quantity)

    class Meta:
        verbose_name: str = "Regular Order Record"
        verbose_name_plural: str = "Regular Order Records"


class CustomerRegularOrderRecord(BaseCustomerOrderRecord):
    orders = models.ManyToManyField(RegularOrderRecord)

    @property
    def get_total_price(self) -> float():
        """f(n) = n . Linear Function"""
        res_: int = 0
        for order in self.orders.all():
            res_ += order.total
        return res_

    @property
    def get_orders_detail(self):
        """f(n) = n . Linear Function"""
        res: List = []
        [
            res.append(
                {
                    "order_id": order.id,
                    "item_name": order.item.item.name,
                    "ordered_quantity": order.quantity,
                    "price_per_item": float(order.item.selling_price_per_item),
                    "order_total_price": order.total,
                    "order_number": order.order_number,
                    "created_by": order.created_by.username,
                    "date_created": order.date_created,
                },
            )
            for order in self.orders.all()
        ]
        return res

    class Meta:
        verbose_name = "Customer Regular Order Record"
        verbose_name_plural = "Customer Regular Order Records"


class CustomerRegularOrderRecordPayment(BasePayment):
    customer_order_record = models.ForeignKey(
        CustomerRegularOrderRecord, on_delete=models.CASCADE
    )

    def __str__(self) -> str():
        """f(n) = c; c=1 Constant Function"""
        return "{}: Payment Status: {}".format(
            self.customer_order_record, self.payment_status.title()
        )

    @property
    def get_total_amount_to_pay(self):
        return float(self.customer_order_record.get_total_price)

    @property
    def get_remaining_amount(self):
        return float(self.get_total_amount_to_pay - self.amount_paid)

    class Meta:
        verbose_name: str = "Customer Regular Order Record Payment"
        verbose_name_plural: str = "Customer Regular Order Record Payments"


class CreditCustomerRegularOrderRecordPayment(BaseCreditCustomerPayment):
    record_order_payment_record = models.ForeignKey(
        CustomerRegularOrderRecordPayment, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name: str = "Credit Customer Regular Order Record Payment"
        verbose_name_plural: str = "Credit Customer Regular Order Record Payments"


class CreditCustomerRegularOrderRecordPaymentHistory(models.Model):
    credit_customer_payment = models.ForeignKey(
        CreditCustomerRegularOrderRecordPayment, on_delete=models.CASCADE
    )  # Filter all dishes with 'by_credit'=True and 'customer_dish_payment__payment_status' !="paid"
    amount_paid = models.PositiveIntegerField()
    date_paid = models.DateField()
    objects = Manager()

    def __str__(self):
        return self.credit_customer_payment.customer.customer_name

    class Meta:
        ordering: list = ["-id"]
        verbose_name: str = "Credit Customer Regular Order Record Payment History"
        verbose_name_plural: str = (
            "Credit Customer Regular Order Record Payment Histories"
        )


class CreditCustomerTequilaOrderRecordPayment(BaseCreditCustomerPayment):
    record_order_payment_record = models.ForeignKey(
        CustomerTequilaOrderRecordPayment, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name: str = "Credit Customer Tequila Order Record Payment"
        verbose_name_plural: str = "Credit Customer Tequila Order Record Payments"


class CreditCustomerTequilaOrderRecordPaymentHistory(models.Model):
    credit_customer_payment = models.ForeignKey(
        CreditCustomerTequilaOrderRecordPayment, on_delete=models.CASCADE
    )  # Filter all dishes with 'by_credit'=True and 'customer_dish_payment__payment_status' !="paid"
    amount_paid = models.PositiveIntegerField()
    date_paid = models.DateField()
    objects = Manager()

    def __str__(self):
        return self.credit_customer_payment.customer.customer_name

    class Meta:
        ordering: list = ["-id"]
        verbose_name: str = "Credit Customer Tequila Order Record Payment History"
        verbose_name_plural: str = (
            "Credit Customer Tequila Order Record Payment Histories"
        )


# Payrol Management


class BarPayrol(BasePayrol):
    """Restaurant Payrol"""

    bar_payee = models.ForeignKey(
        User, related_name="bar_payee", on_delete=models.CASCADE
    )
    bar_payer = models.ForeignKey(
        User, related_name="bar_payer", on_delete=models.CASCADE
    )

    def __str__(self):

        return f"{self.bar_payee.username} Paid: {self.amount_paid}"
