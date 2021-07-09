from core.models import BaseConfig, BaseInventory, Item
from django.db.models.aggregates import Sum
from django.db.models.manager import Manager
from user.models import User
from django.db import models

# Inventory


class MainInventoryItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount_per_unit = models.PositiveIntegerField(
        default=0, help_text="e.g 4 Plates per 1 Kg"
    )
    price_per_unit = models.PositiveIntegerField(
        default=0, help_text="e.g 1200 per 1 plate"
    )
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
    threshold = models.IntegerField(default=0)

    def __str__(self) -> str():
        """String representation of object

        Returns:
                str: name
        """
        return self.main_inventory_item.item.name


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
    order_number = models.CharField(
        max_length=255, null=True, blank=True, unique=True, help_text="Leave blank"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    class Meta:
        abstract: bool = True


class RestaurantCustomerOrder(BaseCustomerOrder):
    """single customer order"""

    sub_menu = models.ForeignKey(Menu, on_delete=models.CASCADE)

    def __str__(self) -> str():
        return f"{self.sub_menu.name} Order#{self.order_number}"

    class Meta:
        ordering: list = ["-id"]
        verbose_name = "Restaurant Customer Order"
        verbose_name_plural = "Restaurant Customer Orders"


class CustomerDish(models.Model):
    """Customer Dish class"""

    customer_name = models.CharField(max_length=255)
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
        return self.orders.all().aggregate(total=Sum("sub_menu__price"))

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


class CustomerDishPayment(models.Model):
    """customer dish payment class"""

    customer_dish = models.ForeignKey(CustomerDish, on_delete=models.CASCADE)
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

    def __str__(self) -> str():
        return f"{self.customer_dish}: Payment Status{self.payment_status}"

    @property
    def get_total_amount_to_pay(self) -> float():
        return self.customer_dish.get_total_price["total"]
    
    @property
    def get_remaining_amount(self) -> float():
        return self.get_total_amount_to_pay - self.amount_paid

    class Meta:
        ordering: list = ["-id"]
        verbose_name = "Customer Dish Payment"
        verbose_name_plural = "Customer Dish Payments"
