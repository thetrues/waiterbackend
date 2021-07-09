from django.db.models.manager import Manager
from abc import abstractmethod
from django.db import models


class BaseInventory(models.Model):
    quantity = models.PositiveIntegerField(default=0)
    purchasing_price = models.PositiveIntegerField(default=0)
    date_purchased = models.DateTimeField()
    date_perished = models.DateTimeField(null=True, blank=True)
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
