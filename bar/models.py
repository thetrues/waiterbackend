from django.db.models.aggregates import Sum
from django.db.models.manager import Manager
from typing import Dict, List, Set
from user.models import User
from django.db import models
from core.models import (
    BaseCreditCustomerPayment,
    BaseCustomerOrderRecord,
    BaseOrderRecord,
    BaseInventory,
    BasePayment,
    BasePayrol,
    Item,
)

# Inventory Management


class RegularInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_items = models.IntegerField()
    selling_price_per_item = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self) -> str:
        return str(self.item)

    def estimate_sales(self) -> float:
        return self.selling_price_per_item * self.total_items

    def estimate_profit(self) -> float:
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Regular Inventory Record"
        verbose_name_plural: str = "Regular Inventory Records"


class TekilaInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_shots_per_tekila = models.IntegerField()
    selling_price_per_shot = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self) -> str:
        return self.item.name

    def estimate_sales(self) -> float:
        return self.selling_price_per_shot * self.total_shots_per_tekila * self.quantity

    def estimate_profit(self) -> float:
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Tequila Inventory Record"
        verbose_name_plural: str = "Tequila Inventory Records"


# Sale Management


class TequilaOrderRecord(BaseOrderRecord):
    item = models.ForeignKey(TekilaInventoryRecord, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.item.item.name

    @property
    def total(self) -> float:
        return float(self.item.selling_price_per_shot * self.quantity)

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Tequila Order Record"
        verbose_name_plural: str = "Tequila Order Records"


class CustomerTequilaOrderRecord(BaseCustomerOrderRecord):
    orders = models.ManyToManyField(TequilaOrderRecord)

    @property
    def get_total_price(self) -> float:
        """f(n) = n . Linear Function"""
        res_: float = 0.0
        for order in self.orders.all():
            res_ += order.total
        return res_

    def get_payment_status(self) -> str:
        total_payment: float = self.get_paid_amount()

        if total_payment and total_payment >= self.get_total_price:
            payment_status: str = "Fully Paid"
        elif total_payment and self.get_total_price <= 0 or not total_payment:
            payment_status: str = "Not Paid"
        else:
            payment_status: str = "Partially Paid"

        return payment_status

    def get_paid_amount(self) -> float:
        paid_amount: float = self.customertequilaorderrecordpayment_set.aggregate(
            total=Sum("amount_paid")
        )["total"]

        return paid_amount or 0.0

    def get_remained_amount(self) -> float:
        paid_amount: float = self.get_paid_amount()

        if paid_amount:
            return self.get_total_price - self.get_paid_amount()
        return self.get_total_price

    @property
    def get_orders_detail(self) -> List[Dict]:
        """f(n) = n . Linear Function"""
        res: List[Dict] = []
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
                    "date_created": str(order.date_created).split(" ")[0],
                    "time_created": str(order.date_created).split(" ")[1].split(".")[0],
                },
            )
            for order in self.orders.all()
        ]

        return res

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Regular Order Record"
        verbose_name_plural: str = "Customer Regular Order Records"


class CustomerTequilaOrderRecordPayment(BasePayment):
    """CustomerTequilaOrderRecordPayment Class"""

    customer_order_record = models.ForeignKey(
        CustomerTequilaOrderRecord, on_delete=models.CASCADE
    )

    def change_payment_status(self):
        if self.amount_paid == 0:
            self.payment_status = "unpaid"
        elif self.amount_paid >= self.get_total_amount_to_pay:
            self.payment_status = "paid"
        else:
            self.payment_status = "partial"
        self.save()

    def __str__(self) -> str:
        """f(n) = c; c=1 Constant Function"""

        return "{}: Payment Status: {}".format(
            self.customer_order_record, self.payment_status.title()
        )

    @property
    def get_total_amount_to_pay(self) -> float:

        return float(self.customer_order_record.get_total_price)

    @property
    def get_remaining_amount(self) -> float:

        return float(self.get_total_amount_to_pay - self.amount_paid)

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Tequila Order Record Payment"
        verbose_name_plural: str = "Customer Tequila Order Record Payments"


class RegularOrderRecord(BaseOrderRecord):
    item = models.ForeignKey(RegularInventoryRecord, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.item.item.name

    @property
    def total(self) -> float:
        return float(self.item.selling_price_per_item * self.quantity)

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Regular Order Record"
        verbose_name_plural: str = "Regular Order Records"


class CustomerRegularOrderRecord(BaseCustomerOrderRecord):
    orders = models.ManyToManyField(RegularOrderRecord)

    @property
    def get_total_price(self) -> float:
        """f(n) = n . Linear Function"""
        res_: float = 0.0
        for order in self.orders.all():
            res_ += order.total

        return res_

    @property
    def get_orders_detail(self) -> List[Dict]:
        """f(n) = n . Linear Function"""
        res: List[Dict] = []
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
                    "date_created": str(order.date_created).split(" ")[0],
                    "time_created": str(order.date_created).split(" ")[1].split(".")[0],
                },
            )
            for order in self.orders.all()
        ]

        return res

    def get_payment_status(self) -> str:
        total_payment: float = self.get_paid_amount()

        if total_payment and total_payment >= self.get_total_price:
            payment_status: str = "Fully Paid"
        elif total_payment and self.get_total_price <= 0 or not total_payment:
            payment_status: str = "Not Paid"
        else:
            payment_status: str = "Partially Paid"

        return payment_status

    def get_paid_amount(self) -> float:
        paid_amount: float = self.customerregularorderrecordpayment_set.aggregate(
            total=Sum("amount_paid")
        )["total"]

        if paid_amount:
            return paid_amount
        else:
            return 0.0

    def get_remained_amount(self) -> float:
        paid_amount: float = self.get_paid_amount()

        if paid_amount:
            return self.get_total_price - self.get_paid_amount()
        return self.get_total_price

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Regular Order Record"
        verbose_name_plural: str = "Customer Regular Order Records"


class CustomerRegularOrderRecordPayment(BasePayment):
    customer_order_record = models.ForeignKey(
        CustomerRegularOrderRecord, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
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
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Regular Order Record Payment"
        verbose_name_plural: str = "Customer Regular Order Record Payments"


class CreditCustomerRegularOrderRecordPayment(BaseCreditCustomerPayment):
    record_order_payment_record = models.ForeignKey(
        CustomerRegularOrderRecordPayment, on_delete=models.CASCADE
    )

    def get_credit_payable_amount(self) -> float:
        dish_total_price: float = (
            self.record_order_payment_record.customer_order_record.get_total_price
        )

        return dish_total_price - self.amount_paid

    class Meta:
        ordering: List[str] = ["-id"]
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
        ordering: List[str] = ["-id"]
        verbose_name: str = "Credit Customer Regular Order Record Payment History"
        verbose_name_plural: Set[
            str
        ] = "Credit Customer Regular Order Record Payment Histories"


class CreditCustomerTequilaOrderRecordPayment(BaseCreditCustomerPayment):
    record_order_payment_record = models.ForeignKey(
        CustomerTequilaOrderRecordPayment, on_delete=models.CASCADE
    )

    def get_credit_payable_amount(self) -> float:
        dish_total_price: float = (
            self.record_order_payment_record.customer_order_record.get_total_price
        )
        if self.amount_paid:
            return dish_total_price - self.amount_paid

        return 0.0

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
        return self.credit_customer_payment.customer.name

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Credit Customer Tequila Order Record Payment History"
        verbose_name_plural: str = (
            "Credit Customer Tequila Order Record Payment Histories"
        )


### Start Major Changes


class RegularTequilaOrderRecord(models.Model):
    regular_items = models.ManyToManyField(RegularOrderRecord)
    tequila_items = models.ManyToManyField(TequilaOrderRecord)
    order_number = models.CharField(max_length=10, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    def __str__(self) -> str:

        return "Bar Order Number: %s" % self.order_number

    def get_total_price(self) -> float:
        res_: float = 0.0
        for r_order in self.regular_items.all():
            res_ += r_order.total

        for t_order in self.tequila_items.all():
            res_ += t_order.total

        return res_

    def get_regular_items_details(self) -> List[Dict]:
        regular_items: List[Dict] = []
        [
            regular_items.append(
                {
                    "order_id": order.id,
                    "item_name": order.item.item.name,
                    "ordered_quantity": order.quantity,
                    "price_per_item": float(order.item.selling_price_per_item),
                    "order_total_price": order.total,
                    "order_number": order.order_number,
                    "created_by": order.created_by.username,
                    "date_created": str(order.date_created).split(" ")[0],
                    "time_created": str(order.date_created).split(" ")[1].split(".")[0],
                },
            )
            for order in self.regular_items.all()
        ]

        return regular_items

    def get_tequila_items_details(self) -> List[Dict]:
        tequila_items: List[Dict] = []
        [
            tequila_items.append(
                {
                    "order_id": order.id,
                    "item_name": order.item.item.name,
                    "ordered_quantity": order.quantity,
                    "price_per_shot": float(order.item.selling_price_per_shot),
                    "order_total_price": order.total,
                    "order_number": order.order_number,
                    "created_by": order.created_by.username,
                    "date_created": str(order.date_created).split(" ")[0],
                    "time_created": str(order.date_created).split(" ")[1].split(".")[0],
                },
            )
            for order in self.tequila_items.all()
        ]

        return tequila_items

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Regular and Tequila Order Record"
        verbose_name_plural: str = "Regular and Tequila Order Records"


class CustomerRegularTequilaOrderRecord(BaseCustomerOrderRecord):
    regular_tequila_order_record = models.ForeignKey(
        RegularTequilaOrderRecord, on_delete=models.CASCADE
    )

    def __str__(self) -> str:

        return "Customer Orders Number: %s" % self.customer_orders_number

    def get_payment_status(self) -> str:
        total_payment: float = self.get_paid_amount()

        if (
            total_payment
            and total_payment >= self.regular_tequila_order_record.get_total_price
        ):
            payment_status: str = "Fully Paid"
        elif (
            total_payment
            and self.regular_tequila_order_record.get_total_price <= 0
            or not total_payment
        ):
            payment_status: str = "Not Paid"
        else:
            payment_status: str = "Partially Paid"

        return payment_status

    def get_paid_amount(self) -> float:
        paid_amount: float = (
            self.customerregulartequilaorderrecordpayment_set.aggregate(
                total=Sum("amount_paid")
            )["total"]
        )

        return paid_amount or 0.0

    def get_remained_amount(self) -> float:
        paid_amount: float = self.get_paid_amount()

        if paid_amount:
            return (
                self.regular_tequila_order_record.get_total_price
                - self.get_paid_amount()
            )
        return self.regular_tequila_order_record.get_total_price

    @property
    def get_orders_detail(self) -> Dict:

        res: Dict = {}
        res["order_total_price"] = self.regular_tequila_order_record.get_total_price()

        orders: List = []
        orders.append(self.regular_tequila_order_record.get_regular_items_details())
        orders.append(self.regular_tequila_order_record.get_tequila_items_details())

        res["orders"] = orders

        return res

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Regular Order Record"
        verbose_name_plural: str = "Customer Regular Order Records"


class CustomerRegularTequilaOrderRecordPayment(BasePayment):
    customer_regular_tequila_order_record = models.ForeignKey(
        CustomerRegularTequilaOrderRecord, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        """f(n) = c; c=1 Constant Function"""
        return "{}: Payment Status: {}".format(
            self.customer_regular_tequila_order_record, self.payment_status.title()
        )

    @property
    def get_total_amount_to_pay(self):
        return float(
            self.customer_regular_tequila_order_record.regular_tequila_order_record.get_total_price
        )

    @property
    def get_remaining_amount(self):
        return float(self.get_total_amount_to_pay - self.amount_paid)

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Regular Order Record Payment"
        verbose_name_plural: str = "Customer Regular Order Record Payments"


class CreditCustomerRegularTequilaOrderRecordPayment(BaseCreditCustomerPayment):
    record_order_payment_record = models.ForeignKey(
        CustomerRegularTequilaOrderRecordPayment, on_delete=models.CASCADE
    )

    def get_credit_payable_amount(self) -> float:
        dish_total_price: float = (
            self.record_order_payment_record.customer_regular_tequila_order_record.regular_tequila_order_record.get_total_price
        )

        return dish_total_price - self.amount_paid

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Credit Customer Regular Order Record Payment"
        verbose_name_plural: str = "Credit Customer Regular Order Record Payments"


class CreditCustomerRegularTequilaOrderRecordPaymentHistory(models.Model):
    credit_customer_payment = models.ForeignKey(
        CreditCustomerRegularTequilaOrderRecordPayment, on_delete=models.CASCADE
    )  # Filter all dishes with 'by_credit'=True and 'customer_dish_payment__payment_status' !="paid"
    amount_paid = models.PositiveIntegerField()
    date_paid = models.DateField()
    objects = Manager()

    def __str__(self):
        return self.credit_customer_payment.customer.name

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = (
            "Credit Customer Regular and Tequila Order Record Payment History"
        )
        verbose_name_plural: str = (
            "Credit Customer Regular and Tequila Order Record Payment Histories"
        )


### End Major Changes


# Payrol Management


class BarPayrol(BasePayrol):
    """Restaurant Payrol"""

    bar_payee = models.ForeignKey(
        User, related_name="bar_payee", on_delete=models.CASCADE
    )
    bar_payer = models.ForeignKey(
        User, related_name="bar_payer", on_delete=models.CASCADE
    )

    def __str__(self) -> str:

        return f"{self.bar_payee.username} Paid: {self.amount_paid}"
