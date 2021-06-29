from django.db.models.manager import Manager
from user.models import User
from django.db import models


ITEM_UNITS: set = (
    ("kilogram", "Kilogram"),
    ("litre", "Litre"),
    ("crate", "Crate"),
    ("carton", "Carton"),
    ("piece", "Piece"),
    ("tray", "Tray"),
)


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

    unit = models.CharField(max_length=10, choices=ITEM_UNITS)


class InventoryRecord(models.Model):
    """[summary]

    Args:
            models ([type]): [description]
    """

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.FloatField()
    price = models.FloatField()
    threshold = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    objects = Manager()

    def __str__(self) -> str:
        """String representation of InventoryRecord object

        Returns:
                str: item.__repr__()
        """
        return str(self.item)

    class Meta:
        ordering: set = ("-id",)
        indexes: list = [
            models.Index(
                fields=[
                    "item",
                ]
            ),
        ]


class DailyStock(models.Model):
    """[summary]

    Args:
            models ([type]): [description]
    """

    inventoryrecord = models.ForeignKey(InventoryRecord, on_delete=models.CASCADE)
    quantity = models.FloatField()
    date_created = models.DateField()
    time_created = models.TimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    objects = Manager()

    def __str__(self) -> str:
        """String representation of DailyStock object

        Returns:
                str: inventoryrecord.__repr__()
        """
        return str(self.inventoryrecord)

    class Meta:
        ordering: set = ("-id",)
        indexes: list = [
            models.Index(
                fields=[
                    "inventoryrecord",
                ]
            ),
        ]


class Menu(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    price = models.FloatField()


class Additive(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    pass


class Order(models.Model):
    """[summary]

    Args:
            models ([type]): [description]
    """

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    additives = models.ManyToManyField(Additive, blank=True)
    objects = Manager()

    def __str__(self):
        """[summary]

        Returns:
                [type]: [description]
        """
        return str(self.menu)

    class Meta:
        ordering: set = ("-id",)
        indexes: list = [
            models.Index(
                fields=[
                    "menu",
                ]
            ),
        ]


class CompleteOrder(models.Model):
    """[summary]

    Args:
            models ([type]): [description]
    """

    order = models.ManyToManyField(Order)
    customer_name = models.CharField(max_length=255)
    order_number = models.CharField(max_length=255, unique=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    objects = Manager()

    def __str__(self):
        """[summary]

        Returns:
                [type]: [description]
        """
        return f"{self.customer_name} menu list"

    class Meta:
        ordering: set = ("-id",)
        indexes: list = [
            models.Index(
                fields=[
                    "customer_name",
                    "order_number",
                ]
            ),
        ]
