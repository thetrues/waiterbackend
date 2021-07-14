from core.models import BaseInventory, BasePayment, Item
from user.models import User
from django.db import models

# Inventory Management


class RegularInventoryRecord(BaseInventory):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_items = models.IntegerField()
    selling_price_per_item = models.IntegerField()

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

    def __str__(self):
        return self.item.name

    def estimate_sales(self) -> float():
        return self.selling_price_per_shot * self.total_shots_per_tekila * self.quantity

    def estimate_profit(self) -> float():
        return self.estimate_sales() - self.purchasing_price

    class Meta:
        ordering: list = ["-id"]
        verbose_name: str = "Tekila Inventory Record"
        verbose_name_plural: str = "Tekila Inventory Records"


# Sale Management


class OrderRecord(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    order_number = models.CharField(max_length=8, null=True, blank=True)

    @property
    def total(self) -> float():
        return self.item.price * self.quantity

    def __str__(self) -> str():
        return self.item.name

    class Meta:
        ordering: list = ["-id"]
        verbose_name: str = "Order Record"
        verbose_name_plural: str = "Order Records"
        indexes: list = [
            models.Index(fields=["item", "order_number"]),
        ]


class CustomerOrderRecord(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=14, null=True, blank=True)
    orders = models.ManyToManyField(OrderRecord)
    customer_orders_number = models.CharField(max_length=8, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def get_total_price(self) -> float():
        res_: int = 0
        for order in self.orders.all():
            res_ += order.total
        return res_

    @property
    def get_orders_detail(self) -> float():
        res: list = []
        [
            res.append(
                {
                    "item": order.item.name,
                    "price": order.item.price,
                },
            )
            for order in self.orders.all()
        ]
        return res

    def __str__(self) -> str():
        return (
            f"{self.customer_name}: CustomerOrderRecord#{self.customer_orders_number}"
        )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Customer Order Record"
        verbose_name_plural = "Customer Order Records"
        indexes: list = [
            models.Index(fields=["customer_name", "created_by"]),
        ]


class CustomerOrderRecordPayment(BasePayment):
    customer_order_record = models.ForeignKey(
        CustomerOrderRecord, on_delete=models.CASCADE
    )

    def __str__(self) -> str():
        return f"{self.customer_order_record}: Payment Status{self.payment_status}"

    @property
    def get_total_amount_to_pay(self) -> float():
        return self.customer_order_record.get_total_price

    @property
    def get_remaining_amount(self) -> float():
        return self.get_total_amount_to_pay - self.amount_paid
