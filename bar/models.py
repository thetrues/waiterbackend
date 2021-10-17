from typing import Dict, List, Set

from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.manager import Manager

from bar.managers import BarPayrolCustomManager
from core.models import (
    BaseCreditCustomerPayment,
    BaseCustomerOrderRecord,
    BaseOrderRecord,
    BaseInventory,
    BasePayment,
    BasePayrol,
    Item,
)
from user.models import User


# Inventory Management


class RegularInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_items = models.IntegerField()
    selling_price_per_item = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self) -> str:
        return str(self.item)

    def format_name_unit(self) -> str:
        return self.item.name + " " + self.item.unit.name

    def estimate_sales(self) -> float:  # 4778800 - 61200 = 4717600
        return self.actual_selling()

    def actual_selling(self) -> int:  # 1800 * 266 = 478800
        return self.selling_price_per_item * self.actual_items()

    def actual_items(self) -> int:  # 300 - 34 = 266
        return self.total_items - self.total_broken_items()

    def estimate_profit(self) -> float:  # 450000 - 4717600 = 4267600
        return self.estimate_sales() - self.purchasing_price

    def total_broken_items(self) -> int:  # 34
        return self.regularinventoryrecordbroken_set.aggregate(total=Sum("quantity_broken"))[
                   "total"] or 0

    # def total_cost_for_broken_item(self) -> int:  # 34 * 1800 = 61200
    #     return self.total_broken_items() * self.selling_price_per_item

    def get_price_of_items(self, item_quantity) -> int:
        return int(item_quantity * self.selling_price_per_item)

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Regular Inventory Record"
        verbose_name_plural: str = "Regular Inventory Records"


class RegularInventoryRecordsTrunk(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    regular_inventory_record = models.ManyToManyField(RegularInventoryRecord)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    objects = Manager()

    def __str__(self) -> str:
        return f"Regular Inventory Record Trunk For {self.item.name}"

    def get_last_inventory_record(self):  # -> RegularInventoryRecord
        records = self.regular_inventory_record.select_related("item")[::-1]
        for record in records:
            if record.stock_status == "available" and record.available_quantity > 0:
                return record
            else:
                continue

    @property
    def total_items_added(self) -> int:
        return self.regular_inventory_record.aggregate(total=Sum("total_items"))["total"] or 0

    @property
    def total_items_available(self) -> int:
        return self.get_total_available_items() or 0

    @property  # This should be handled per request
    def issued_stocks(self) -> Dict:
        return {}

    @property  # This should be handled per request
    def stocks_in(self) -> Dict:
        return {}

    def get_total_available_items(self) -> int:
        return self.regular_inventory_record.aggregate(total=Sum("available_quantity"))["total"]

    @property
    def stock_status(self) -> str:
        return "Available" if self.get_total_available_items() else "Unavailable"

    def get_stock_in(self) -> List[Dict]:
        stock_in: List[Dict] = []
        for record in self.regular_inventory_record.select_related("item", "item__unit"):
            temp_stock_in: Dict = {
                "id": record.id,
                "quantity": record.item.unit.name + str(record.quantity),
                "total_items": record.total_items,
                "total_broken_items": record.total_broken_items(),
                "purchasing_price": record.purchasing_price,
                "selling_price_per_item": record.selling_price_per_item,
                "available_items": record.available_quantity,
                "threshold": record.threshold,
                "estimated_sales": record.estimate_sales(),
                "estimated_profit": record.estimate_profit(),
                "stock_status": record.get_stock_status_display(),
                "date_purchased": record.date_purchased.__str__(),
                "date_perished": record.date_perished.__str__(),
                "broken_items": record.regularinventoryrecordbroken_set.values("quantity_broken", "created_at"),
            }
            stock_in.append(temp_stock_in)

        return stock_in

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Regular Inventory Records Trunk"
        verbose_name_plural: str = "Regular Inventory Records Trunks"


class RegularInventoryRecordBroken(models.Model):
    regular_inventory_record = models.ForeignKey(RegularInventoryRecord, on_delete=models.CASCADE)
    quantity_broken = models.PositiveIntegerField()
    created_at = models.DateField(auto_now_add=True)
    objects = Manager()

    def __str__(self) -> str:
        return f"Regular Inventory Record Broken For {self.regular_inventory_record.item.name}"

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Regular Inventory Record Broken"
        verbose_name_plural: str = "Regular Inventory Records Broken"


class TekilaInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_shots_per_tekila = models.IntegerField()
    selling_price_per_shot = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self) -> str:
        return self.item.name

    def format_name_unit(self) -> str:
        return self.item.name + " " + self.item.unit.name

    def estimate_sales(self) -> float:
        return self.selling_price_per_shot * self.total_shots_per_tekila * self.quantity

    def estimate_profit(self) -> float:
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Tequila Inventory Record"
        verbose_name_plural: str = "Tequila Inventory Records"


class TequilaInventoryRecordsTrunk(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    tequila_inventory_record = models.ManyToManyField(TekilaInventoryRecord)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    objects = Manager()

    def __str__(self) -> str:
        return f"Tequila Inventory Record Trunk For {self.item.name}"

    def get_last_inventory_record(self):  # -> TequilaInventoryRecord
        records = self.tequila_inventory_record.select_related("item")[::-1]
        for record in records:
            if record.stock_status == "available" and record.available_quantity > 0:
                return record
            else:
                continue

    @property
    def total_items_added(self) -> int:
        return self.tequila_inventory_record.aggregate(total=Sum("total_shots_per_tekila"))["total"] or 0

    @property
    def total_items_available(self) -> int:
        return self.get_total_available_items() or 0

    @property  # This should be handled per request
    def issued_stocks(self) -> Dict:
        return {}

    @property  # This should be handled per request
    def stocks_in(self) -> Dict:
        return {}

    def get_total_available_items(self) -> int:
        return self.tequila_inventory_record.aggregate(total=Sum("available_quantity"))["total"]

    @property
    def stock_status(self) -> str:
        return "Available" if self.get_total_available_items() else "Unavailable"

    def get_stock_in(self) -> List[Dict]:
        stock_in: List[Dict] = []
        # counter = 1
        for record in self.tequila_inventory_record.all():
            temp_stock_in: Dict = {
                "id": record.id,
                "total_shots": record.total_shots_per_tekila,
                "selling_price_per_item": record.selling_price_per_item,
                "available_items": record.available_quantity,
                "threshold": record.threshold,
                "estimated_sales": record.estimate_sales(),
                "estimated_profit": record.estimate_profit(),
                "stock_status": record.get_stock_status_display(),
                "date_purchased": record.date_purchased.__str__(),
                "date_perished": record.date_perished.__str__(),
                "broken_items": record.tequilainventoryrecordbroken_set.values("quantity_broken", "created_at"),
            }
            stock_in.append(temp_stock_in)
            # counter += 1

        return stock_in

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Tequila Inventory Records Trunk"
        verbose_name_plural: str = "Tequila Inventory Records Trunks"


class TequilaInventoryRecordBroken(models.Model):
    tequila_inventory_record = models.ForeignKey(TekilaInventoryRecord, on_delete=models.CASCADE)
    quantity_broken = models.PositiveIntegerField()
    created_at = models.DateField(auto_now_add=True)
    objects = Manager()

    def __str__(self) -> str:
        return f"Tequila Inventory Record Broken For {self.tequila_inventory_record.item.name}"

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Tequila Inventory Record Broken"
        verbose_name_plural: str = "Tequila Inventory Records Broken"


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
    def total(self) -> int:
        return self.item.selling_price_per_item * self.quantity

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Regular Order Record"
        verbose_name_plural: str = "Regular Order Records"


class CustomerRegularOrderRecord(BaseCustomerOrderRecord):
    orders = models.ManyToManyField(RegularOrderRecord)

    @property
    def get_total_price(self) -> int:
        """f(n) = n . Linear Function"""
        res_: int = 0
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

    def get_paid_amount(self) -> int:
        paid_amount: int = self.customerregularorderrecordpayment_set.aggregate(
            total=Sum("amount_paid")
        )["total"]

        if paid_amount:
            return paid_amount
        else:
            return 0

    def get_remained_amount(self) -> int:
        paid_amount: int = self.get_paid_amount()

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
    def get_total_amount_to_pay(self) -> int:
        return self.customer_order_record.get_total_price

    @property
    def get_remaining_amount(self) -> int:
        return self.get_total_amount_to_pay - self.amount_paid

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Regular Order Record Payment"
        verbose_name_plural: str = "Customer Regular Order Record Payments"


class CreditCustomerRegularOrderRecordPayment(BaseCreditCustomerPayment):
    record_order_payment_record = models.ForeignKey(
        CustomerRegularOrderRecordPayment, on_delete=models.CASCADE
    )

    def get_credit_payable_amount(self) -> int:
        dish_total_price: int = self.record_order_payment_record.customer_order_record.get_total_price

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


# Start Major Changes

class RegularTequilaOrderRecord(models.Model):
    regular_items = models.ManyToManyField(RegularOrderRecord)
    tequila_items = models.ManyToManyField(TequilaOrderRecord)
    order_number = models.CharField(max_length=10, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    def __str__(self) -> str:

        return "Bar Order Number: %s" % self.order_number

    def get_total_price(self) -> int:
        res_: int = 0
        for r_order in self.regular_items.all():
            res_ += r_order.total

        for t_order in self.tequila_items.all():
            res_ += t_order.total

        return res_

    def get_regular_items_details(self) -> List:
        regular_items: List = []
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

    def get_tequila_items_details(self) -> List:
        tequila_items: List = []
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

    @property
    def dish_number(self):
        return self.customer_orders_number

    @property
    def paid_amount(self):
        return self.get_paid_amount()

    @property
    def payable_amount(self):
        return self.regular_tequila_order_record.get_total_price()

    @property
    def remained_amount(self) -> int:
        paid_amount: int = self.get_paid_amount()

        if paid_amount:
            return (
                    self.regular_tequila_order_record.get_total_price()
                    - self.get_paid_amount()
            )
        return self.regular_tequila_order_record.get_total_price()

    @property
    def orders(self):
        res: Dict = {"total_price": self.regular_tequila_order_record.get_total_price()}

        orders: Dict = {
            "drinks": self.regular_tequila_order_record.get_regular_items_details(),
            "shots": self.regular_tequila_order_record.get_tequila_items_details()
        }

        res["order_structures"] = orders

        return res

    @property
    def payment_status(self) -> str:
        total_payment: int = self.get_paid_amount()

        if (
                total_payment
                and total_payment >= self.regular_tequila_order_record.get_total_price()
        ):
            payment_status: str = "Fully Paid"
        elif (
                total_payment
                and self.regular_tequila_order_record.get_total_price() <= 0
                or not total_payment
        ):
            payment_status: str = "Not Paid"
        else:
            payment_status: str = "Partially Paid"

        return payment_status

    def get_total_price(self) -> float:
        return self.regular_tequila_order_record.get_total_price()

    def get_payment_status(self) -> str:
        total_payment: int = self.get_paid_amount()

        if (
                total_payment
                and total_payment >= self.regular_tequila_order_record.get_total_price()
        ):
            payment_status: str = "Fully Paid"
        elif (
                total_payment
                and self.regular_tequila_order_record.get_total_price() <= 0
                or not total_payment
        ):
            payment_status: str = "Not Paid"
        else:
            payment_status: str = "Partially Paid"

        return payment_status

    def get_paid_amount(self) -> int:
        paid_amount: int = (
            self.customerregulartequilaorderrecordpayment_set.aggregate(
                total=Sum("amount_paid")
            )["total"]
        )

        return paid_amount or 0

    def get_remained_amount(self) -> int:
        paid_amount: int = self.get_paid_amount()

        if paid_amount:
            return (
                    self.regular_tequila_order_record.get_total_price()
                    - self.get_paid_amount()
            )
        return self.regular_tequila_order_record.get_total_price()

    @property
    def get_orders_detail(self) -> Dict:

        res: Dict = {"total_price": self.regular_tequila_order_record.get_total_price()}

        orders: Dict = {
            "drinks": self.regular_tequila_order_record.get_regular_items_details(),
            "shots": self.regular_tequila_order_record.get_tequila_items_details()
        }

        res["order_structures"] = orders

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
            self.customer_regular_tequila_order_record.regular_tequila_order_record.get_total_price()
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
            self.record_order_payment_record.customer_regular_tequila_order_record.regular_tequila_order_record.get_total_price()
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


# End Major Changes


# Payroll Management


class BarPayrol(BasePayrol):
    """Bar Payroll"""

    bar_payee = models.ForeignKey(
        User, related_name="bar_payee", on_delete=models.CASCADE
    )
    bar_payer = models.ForeignKey(
        User, related_name="bar_payer", on_delete=models.CASCADE
    )
    objects = BarPayrolCustomManager()

    def __str__(self) -> str:
        return f"{self.bar_payee.username} Paid: {self.amount_paid}"
