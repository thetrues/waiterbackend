from core.models import BaseInventory, BasePayment, Item
from django.db.models.manager import Manager
from user.models import User
from django.db import models

# Inventory Management


class RegularInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_items = models.IntegerField()
    selling_price_per_item = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self) -> str():
        return str(self.item)

    def estimate_sales(self):
        return self.selling_price_per_item * self.total_items

    def estimate_profit(self):
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: list = ["-id"]
        verbose_name = "Regular Inventory Record"
        verbose_name_plural = "Regular Inventory Records"


class TekilaInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_shots_per_tekila = models.IntegerField()
    selling_price_per_shot = models.IntegerField()
    threshold = models.IntegerField()

    def __str__(self):
        return self.item.name

    def estimate_sales(self) -> float():
        return self.selling_price_per_shot * self.total_shots_per_tekila * self.quantity

    def estimate_profit(self) -> float():
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: list = ["-id"]
        verbose_name: str = "Tequila Inventory Record"
        verbose_name_plural: str = "Tequila Inventory Records"


# Sale Management


class RegularOrderRecord(models.Model):
    item = models.ForeignKey(RegularInventoryRecord, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    order_number = models.CharField(max_length=8, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    @property
    def total(self):
        return float(self.item.selling_price_per_item * self.quantity)

    def __str__(self) -> str():
        return self.item.item.name

    class Meta:
        ordering: list = ["-id"]
        verbose_name: str = "Regular Order Record"
        verbose_name_plural: str = "Regular Order Records"
        indexes: list = [
            models.Index(fields=["item", "order_number"]),
        ]


class CustomerRegularOrderRecord(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=14, null=True, blank=True)
    orders = models.ManyToManyField(RegularOrderRecord)
    customer_orders_number = models.CharField(max_length=8, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = Manager()

    @property
    def get_total_price(self) -> float():
        """f(n) = n . Linear Function"""
        res_: int = 0
        for order in self.orders.all():
            res_ += order.total
        return res_

    @property
    def get_orders_detail(self):
        """f(n) = n . Linear Function"""
        res: list = []
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
                    "date_created": order.date_created,
                },
            )
            for order in self.orders.all()
        ]
        return res

    def __str__(self) -> str():
        """f(n) = c; c=1 Constant Function"""
        return (
            f"{self.customer_name}: CustomerOrderRecord#{self.customer_orders_number}"
        )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Customer Regular Order Record"
        verbose_name_plural = "Customer Regular Order Records"
        indexes: list = [
            models.Index(fields=["customer_name", "created_by"]),
        ]


class CustomerRegularOrderRecordPayment(BasePayment):
    customer_order_record = models.ForeignKey(
        CustomerRegularOrderRecord, on_delete=models.CASCADE
    )

    def __str__(self) -> str():
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
        ordering: list = ["-id"]
        verbose_name: str = "Customer Regular Order Record Payment"
        verbose_name_plural: str = "Customer Regular Order Record Payments"
