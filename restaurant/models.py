from abc import abstractmethod
from core.models import BaseConfig, BaseInventory, BasePayment, BasePayrol, Item
from django.db.models.manager import Manager
from user.models import User
from django.db import models

# Inventory


class MainInventoryItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount_per_unit = models.PositiveIntegerField(help_text="e.g 4 Plates per 1 Kg")
    price_per_unit = models.PositiveIntegerField(help_text="e.g 1200 per 1 plate")
    objects = Manager()

    def __str__(self) -> str():
        """String representation of object

        Returns:
                str: name
        """
        return self.item.name

    class Meta:
        ordering = ["-id"]


class MainInventoryItemRecord(BaseInventory):
    main_inventory_item = models.ForeignKey(MainInventoryItem, on_delete=models.CASCADE)
    threshold = models.IntegerField()

    def __str__(self) -> str():
        """String representation of object

        Returns:
                str: name
        """
        return self.main_inventory_item.item.name

    @property
    def estimate_sales(self):
        return float(
            self.main_inventory_item.amount_per_unit
            * self.main_inventory_item.price_per_unit
            * self.quantity
        )

    @property
    def estimate_profit(self):
        return float(self.estimate_sales - self.purchasing_price)

    @property
    def stock_out_history(self):
        response: list = []
        [
            response.append(
                {
                    "history_id": _.id,
                    "quantity_out": _.quantity_out,
                    "date_out": _.date_out,
                    "created_by": str(_.created_by),
                }
            )
            for _ in self.maininventoryitemrecordstockout_set.all()
        ]

        return response


class MainInventoryItemRecordStockOut(models.Model):
    item_record = models.ForeignKey(MainInventoryItemRecord, on_delete=models.CASCADE)
    quantity_out = models.PositiveIntegerField()
    date_out = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    objects = Manager()

    def __str__(self):
        return (
            f"{self.item_record.main_inventory_item.item.name}: {self.quantity_out} Out"
        )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Main Inventory Item Record Stock Out"
        verbose_name_plural = "Main Inventory Item Records Stock Out"


class MiscellaneousInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self) -> str():
        """String representation of object

        Returns:
                str: name
        """
        return self.item.name


class Menu(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    description = models.CharField(max_length=255)
    image = models.FileField(upload_to="menu/images/", null=True, blank=True)
    price = models.FloatField()


class Additive(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    pass


# Sales


class BaseCustomerOrder(models.Model):
    """Base customer order class"""

    quantity = models.PositiveIntegerField()
    additives = models.ManyToManyField(Additive)
    order_number = models.CharField(
        max_length=255, null=True, blank=True, unique=True, help_text="Leave blank"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    @property
    @abstractmethod
    def total(self):
        """Returns the total price: i.e sub_menu__price * quantity"""

    class Meta:
        abstract: bool = True


class RestaurantCustomerOrder(BaseCustomerOrder):
    """single customer order"""

    sub_menu = models.ForeignKey(Menu, on_delete=models.CASCADE)

    @property
    def total(self) -> float():
        """Returns the total price: i.e sub_menu__price * quantity"""

        return self.quantity * self.sub_menu.price

    def __str__(self) -> str():
        return f"{self.sub_menu.name} Order#{self.order_number}"

    class Meta:
        ordering: list = ["-id"]
        verbose_name = "Restaurant Customer Order"
        verbose_name_plural = "Restaurant Customer Orders"


class CustomerDish(models.Model):
    """Customer Dish class"""

    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=15, null=True, blank=True)
    orders = models.ManyToManyField(RestaurantCustomerOrder)
    dish_number = models.CharField(
        max_length=255, null=True, blank=True, help_text="Leave blank"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    def __str__(self) -> str():
        return f"{self.customer_name}: Dish#{self.dish_number}"

    @property
    def get_total_price(self) -> float():
        res_: int = 0
        for order in self.orders.all():
            res_ += order.total
        return res_

    @property
    def get_dish_detail(self) -> float():
        res: list = []
        [
            res.append(
                {
                    "sub_menu": order.sub_menu.name,
                    "price": order.sub_menu.price,
                },
            )
            for order in self.orders.all()
        ]
        return res

    class Meta:
        ordering: list = ["-id"]
        verbose_name = "Customer Dish"
        verbose_name_plural = "Customer Dishes"
        unique_together = (("customer_name", "dish_number"),)


class CustomerDishPayment(BasePayment):
    """customer dish payment class"""

    customer_dish = models.ForeignKey(CustomerDish, on_delete=models.CASCADE)

    def __str__(self) -> str():
        return f"{self.customer_dish}: Payment Status{self.payment_status}"

    @property
    def get_total_amount_to_pay(self) -> float():
        return self.customer_dish.get_total_price

    @property
    def get_remaining_amount(self) -> float():
        return self.get_total_amount_to_pay - self.amount_paid


# Payrolling Management


class BarPayrol(BasePayrol):
    """Bar Payrol"""

    bar_payee = models.ForeignKey(
        User, related_name="bar_payee", on_delete=models.CASCADE
    )
    bar_payer = models.ForeignKey(
        User, related_name="bar_payer", on_delete=models.CASCADE
    )

    def __str__(self):

        return f"{self.bar_payee.username} Paid: {self.amount_paid}"
