from django.db.models.manager import Manager
from abc import abstractmethod
from user.models import User
from django.db import models


STOKE_STATUS_CHOICES: set = (
    ("available", "Available"),
    ("unavailable", "Unavailable"),
)


class BaseInventory(models.Model):
    quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField(null=True, blank=True)
    purchasing_price = models.PositiveIntegerField()
    date_purchased = models.DateTimeField()
    date_perished = models.DateTimeField(null=True, blank=True)
    stock_status = models.CharField(
        max_length=11,
        choices=STOKE_STATUS_CHOICES,
        null=True,
        blank=True,
        default="available",
    )
    objects = Manager()

    @abstractmethod
    def estimate_sales(self) -> int():
        """calculations for sales estimation"""

    @abstractmethod
    def estimate_profit(self) -> int():
        """calculations for profit estimation"""

    class Meta:
        abstract: bool = True
        ordering: list = ["-id"]
        indexes: list = [
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
        ordering = ["-id"]
        verbose_name = "Measurement Unit"
        verbose_name_plural = "Measurement Units"

    def __str__(self) -> str():
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

    def __str__(self) -> str():
        """String representation of object

        Returns:
                        str: name
        """
        return self.name

    class Meta:
        abstract: bool = True
        ordering: set = ("-id",)
        indexes: list = [
            models.Index(
                fields=[
                    "name",
                ]
            ),
        ]


ITEM_FOR_TYPE: set = (
    ("bar", "Bar"),
    ("restaurant", "Restaurant"),
)


class Item(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    unit = models.ForeignKey(MeasurementUnit, on_delete=models.CASCADE)
    item_for = models.CharField(max_length=10, choices=ITEM_FOR_TYPE)


PAYMENT_STATUS_CHOICES: set = (
    ("paid", "Fully Paid"),
    ("partial", "Partially Paid"),
    ("unpaid", "Not Paid"),
)

PAYMENT_METHODS: set = (
    ("cash", "Cash"),
    ("mobile", "Mobile Money"),
    ("card", "Credit Card"),
)


class BasePayment(models.Model):
    by_credit = models.BooleanField(default=False)
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
    def __str__(self) -> str():
        """Returns the string representation of this object"""

    class Meta:
        abstract: bool = True
        ordering: list = ["-id"]


class CreditCustomer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=14)
    address = models.CharField(max_length=255)

    def __str__(self):

        return self.name

    class Meta:
        unique_together = ("phone", "name")
        ordering = ["-id"]
        verbose_name = "Credit Customer"
        verbose_name_plural = "Credit Customers"


class BaseCreditCustomerPayment(models.Model):
    customer = models.ForeignKey(CreditCustomer, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    objects = Manager()

    def __str__(self):
        return self.customer.customer_name

    class Meta:
        abstract: bool = True
        ordering: list = ["-id"]


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
    def __str__(self) -> str():
        """Returns the string representation of this object"""

    @abstractmethod
    def get_monthly_payrolls(self) -> float():
        """Returns all payrolls of this month"""

    class Meta:
        abstract: bool = True
        ordering: list = ["-id"]


class BaseOrderRecord(models.Model):
    quantity = models.PositiveIntegerField()
    order_number = models.CharField(max_length=8, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    class Meta:
        abstract: bool = True
        ordering: list = ["-id"]
        indexes: list = [
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
    def get_total_price(self) -> float():
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
        ordering = ["-id"]
        indexes: list = [
            models.Index(fields=["customer_name", "created_by"]),
        ]
