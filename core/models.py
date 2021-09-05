from django.db.models.manager import Manager
from django.db.models.aggregates import Sum
from typing import Dict, List, Set
from abc import abstractmethod
from django.db import models
from django.utils import timezone
from user.models import User


STOKE_STATUS_CHOICES: Set[Set] = (
    ("available", "Available"),
    ("unavailable", "Unavailable"),
)


class BaseInventory(models.Model):
    quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField(null=True, blank=True)
    purchasing_price = models.PositiveIntegerField()
    date_purchased = models.DateField()
    date_perished = models.DateField(null=True, blank=True)
    stock_status = models.CharField(
        max_length=11,
        choices=STOKE_STATUS_CHOICES,
        null=True,
        blank=True,
        default="available",
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

    name = models.CharField(max_length=255, unique=True)
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

    name = models.CharField(max_length=255, unique=True)
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
        indexes: list = [
            models.Index(
                fields=[
                    "name",
                ]
            ),
        ]


ITEM_FOR_TYPE: Set[Set] = (
    ("bar", "Bar"),
    ("restaurant", "Restaurant"),
    ("both", "Both"),
)


class Item(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    unit = models.ForeignKey(MeasurementUnit, on_delete=models.CASCADE)
    item_for = models.CharField(max_length=10, choices=ITEM_FOR_TYPE)


PAYMENT_STATUS_CHOICES: Set[Set] = (
    ("paid", "Fully Paid"),
    ("partial", "Partially Paid"),
    ("unpaid", "Not Paid"),
)

PAYMENT_METHODS: Set[Set] = (
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
    date_paid = models.DateTimeField(auto_now_add=True)
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

    def __str__(self):

        return self.name

    def get_today_balance(self) -> float:
        restaurant_today_spends = self.creditcustomerdishpayment_set.filter(
            date_created=timezone.localdate()
        )
        bar_regular_today_spends = (
            self.creditcustomerregularorderrecordpayment_set.filter(
                date_created=timezone.localdate()
            )
        )
        bar_tequila_today_spends = (
            self.creditcustomertequilaorderrecordpayment_set.filter(
                date_created=timezone.localdate()
            )
        )
        total: float = 0.0
        self.get_restaurant_total(restaurant_today_spends, total)

        self.get_bar_regular_total(bar_regular_today_spends, total)

        total = self.get_bar_tequila_total(bar_tequila_today_spends, total)

        total = self.credit_limit - total

        if total == 0.0:
            total = self.credit_limit

        return total

    def get_bar_tequila_total(self, bar_tequila_today_spends, total):
        for k in bar_tequila_today_spends:
            total += k.get_credit_payable_amount()
        return total

    def get_bar_regular_total(self, bar_regular_today_spends, total):
        for j in bar_regular_today_spends:
            total += j.get_credit_payable_amount()

    def get_restaurant_total(self, restaurant_today_spends, total):
        for i in restaurant_today_spends:
            total += i.get_credit_dish_payable_amount()

    class Meta:
        unique_together: Set[str] = ("phone", "name")
        ordering: List[str] = ["-id"]
        verbose_name: str = "Credit Customer"
        verbose_name_plural: str = "Credit Customers"


class BaseCreditCustomerPayment(models.Model):
    customer = models.ForeignKey(CreditCustomer, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    amount_paid = models.FloatField(null=True, blank=True)
    objects = Manager()

    def __str__(self):
        return self.customer.name

    class Meta:
        abstract: bool = True
        ordering: List[str] = ["-id"]


class BasePayrol(models.Model):
    """Base Payrol Class"""

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
    date_created = models.DateTimeField(auto_now_add=True)
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
