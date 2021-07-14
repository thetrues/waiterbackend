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
    purchasing_price = models.PositiveIntegerField()
    date_purchased = models.DateTimeField()
    date_perished = models.DateTimeField(null=True, blank=True)
    stock_status = models.CharField(
        max_length=11, choices=STOKE_STATUS_CHOICES, null=True, blank=True
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


class Item(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    unit = models.ForeignKey(MeasurementUnit, on_delete=models.CASCADE)


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
        null=True,
        blank=True,
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
        verbose_name: str = "Customer Payment"
        verbose_name_plural: str = "Customer Payments"
