from abc import abstractmethod
from typing import Dict, List, Set

from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.manager import Manager
from django.utils import timezone

from user.models import User

STOCK_STATUS_CHOICES = (
    ("available", "Available"),
    ("unavailable", "Unavailable"),
)


class BaseInventory(models.Model):
    quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField(null=True, blank=True)
    purchasing_price = models.PositiveIntegerField(db_index=True)
    date_purchased = models.DateField(db_index=True)
    date_perished = models.DateField(null=True, blank=True, db_index=True)
    stock_status = models.CharField(
        max_length=11,
        choices=STOCK_STATUS_CHOICES,
        null=True,
        blank=True,
        default="available",
        db_index=True
    )
    objects = Manager()

    @abstractmethod
    def estimate_sales(self) -> int:
        """calculations for sales estimation"""

    @abstractmethod
    def estimate_profit(self) -> int:
        """calculations for profit estimation"""

    def get_orders_history(self, qs) -> Dict:
        orders_history: dict = {}
        self._get_total_ordered_items(orders_history, qs)
        self._get_total_income(orders_history, qs)
        self._get_orders_structure(orders_history, qs)

        return orders_history

    def _get_orders_structure(self, orders_history, qs):
        orders_structure: dict = {}
        temp: List = []
        for item in qs:
            splited_date = str(item.date_created).split(" ")
            orders_structure["order_id"] = item.id
            orders_structure["order_number"] = item.order_number
            orders_structure["quantity"] = item.quantity
            orders_structure["total_price"] = item.total
            orders_structure["date"] = splited_date[0]
            orders_structure["time"] = splited_date[1].split(".")[0]
            orders_structure["created_by"] = item.created_by.username
            temp.append(orders_structure)
            orders_structure: dict = {}

        orders_history["orders_structure"] = temp

    def _get_total_income(self, orders_history, qs):
        total_income: int = 0
        for _ in qs:
            total_income += _.total
        orders_history["total_income"] = total_income

    def _get_total_ordered_items(self, orders_history, qs):
        res: int = qs.aggregate(quantity=Sum("quantity"))["quantity"]
        orders_history["total_ordered_items"] = res or 0

    class Meta:
        abstract: bool = True
        ordering: List[str] = ["-id"]
        indexes: List = [
            models.Index(
                fields=[
                    "quantity",
                ]
            ),
        ]


class MeasurementUnit(models.Model):
    """Measurement Unit Class

    def __str__(self) -> str:
            [str]: [String representation of object name]
    """

    name = models.CharField(max_length=255, unique=True, db_index=True)
    objects = Manager()

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Measurement Unit"
        verbose_name_plural: str = "Measurement Units"

    def __str__(self) -> str:
        """String representation of object

        Returns:
                        str: name
        """
        return self.name


class BaseConfig(models.Model):
    """A base class for common field and __str__()

    Returns:
            [str]: [String representation of object name]
    """

    name = models.CharField(max_length=255, unique=True, db_index=True)
    objects = Manager()

    def __str__(self) -> str:
        """String representation of object

        Returns:
                        str: name
        """
        return self.name

    class Meta:
        abstract: bool = True
        ordering: Set[str] = ("-id",)
        indexes: List = [
            models.Index(
                fields=[
                    "name",
                ]
            ),
        ]


ITEM_FOR_TYPE = (
    ("bar", "Bar"),
    ("restaurant", "Restaurant"),
    ("both", "Both"),
)


class Item(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    unit = models.ForeignKey(MeasurementUnit, on_delete=models.CASCADE, db_index=True)
    item_for = models.CharField(max_length=10, choices=ITEM_FOR_TYPE, db_index=True)
    tequila = models.BooleanField(null=True, db_index=True)  # Regular


PAYMENT_STATUS_CHOICES = (
    ("paid", "Fully Paid"),
    ("partial", "Partially Paid"),
    ("unpaid", "Not Paid"),
)

PAYMENT_METHODS = (
    ("cash", "Cash"),
    ("mobile", "Mobile Money"),
    ("card", "Credit Card"),
)


class BasePayment(models.Model):
    by_credit = models.BooleanField(default=False)
    payment_started = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=7,
        choices=PAYMENT_STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="Leave blank",
    )
    payment_method = models.CharField(
        max_length=6,
        choices=PAYMENT_METHODS,
        default="cash",
        help_text="Leave blank",
    )
    amount_paid = models.IntegerField()
    date_paid = models.DateTimeField()
    date_updated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Leave blank",
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    objects = Manager()

    @abstractmethod
    def __str__(self) -> str:
        """Returns the string representation of this object"""

    class Meta:
        abstract: bool = True
        ordering: List[str] = ["-id"]


class CreditCustomer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=14)
    address = models.CharField(max_length=255)
    credit_limit = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:

        return self.name.__str__()

    def get_today_balance(self) -> int:
        restaurant_today_spends = self.creditcustomerdishpayment_set.filter(
            date_created=timezone.localdate()
        )
        bar_today_spends = (
            self.creditcustomerregulartequilaorderrecordpayment_set.filter(
                date_created=timezone.localdate()
            )
        )

        total: int = 0
        total += self.get_restaurant_total(restaurant_today_spends)

        total += self.get_bar_total(bar_today_spends)

        total_ = self.credit_limit or 0 - total

        if total_ == 0 or total_ > self.credit_limit:
            total_ = self.credit_limit

        return total_ or 0

    def get_bar_total(self, bar_today_spends) -> int:
        bar_teq_total: int = 0
        for k in bar_today_spends:
            bar_teq_total += k.get_credit_payable_amount()

        return bar_teq_total

    def get_restaurant_total(self, restaurant_today_spends) -> int:
        rest_total: int = 0

        for i in restaurant_today_spends:
            rest_total += i.get_credit_dish_payable_amount()

        return rest_total

    class Meta:
        unique_together: Set[str] = ("phone", "name")
        ordering: List[str] = ["-id"]
        verbose_name: str = "Credit Customer"
        verbose_name_plural: str = "Credit Customers"
        indexes = [models.Index(fields=["name", "phone", "address", "credit_limit"])]


class BaseCreditCustomerPayment(models.Model):
    customer = models.ForeignKey(CreditCustomer, on_delete=models.CASCADE)
    date_created = models.DateField()
    amount_paid = models.FloatField(null=True, blank=True)
    objects = Manager()

    def __str__(self):
        return self.customer.name

    class Meta:
        abstract: bool = True
        ordering: List[str] = ["-id"]


class BasePayrol(models.Model):
    """Base Payroll Class"""

    payment_method = models.CharField(
        max_length=6,
        choices=PAYMENT_METHODS,
        default="cash",
        help_text="Leave blank",
    )
    amount_paid = models.FloatField()
    date_paid = models.DateField(auto_now_add=True)
    objects = Manager()

    @abstractmethod
    def __str__(self) -> str:
        """Returns the string representation of this object"""

    @abstractmethod
    def get_monthly_payrolls(self) -> float:
        """Returns all payrolls of this month"""

    class Meta:
        abstract: bool = True
        ordering: List[str] = ["-id"]
        indexes = [
            models.Index(
                fields=[
                    "payment_method",
                    "amount_paid",
                    "date_paid",
                ]
            )
        ]


class BaseOrderRecord(models.Model):
    quantity = models.PositiveIntegerField()
    order_number = models.CharField(max_length=8, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    class Meta:
        abstract: bool = True
        ordering: List[str] = ["-id"]
        indexes: List = [
            models.Index(fields=["item", "order_number"]),
        ]


class BaseCustomerOrderRecord(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=14, null=True, blank=True)
    customer_orders_number = models.CharField(max_length=8, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField()
    objects = Manager()

    @property
    @abstractmethod
    def get_total_price(self) -> float:
        """get total price of all ordered items"""

    @property
    @abstractmethod
    def get_orders_detail(self):
        """get details of all ordered items"""

    def __str__(self):
        """f(n) = c; c=1 Constant Function"""
        return (
            f"{self.customer_name}: CustomerOrderRecord#{self.customer_orders_number}"
        )

    class Meta:
        abstract: bool = True
        ordering: List[str] = ["-id"]
        indexes: List = [
            models.Index(fields=["customer_name", "created_by"]),
        ]


class Expenditure(models.Model):
    name = models.CharField(max_length=128)
    amount = models.IntegerField()
    expenditure_for = models.CharField(
        max_length=10,
        choices=(("bar", "Bar"), ("restaurant", "Restaurant"), ("both", "Both")),
    )
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["name", "amount", "expenditure_for", "date_created"])
        ]
