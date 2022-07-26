from abc import abstractmethod
from typing import Dict, List, Set

from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.manager import Manager

from core.models import (
    BaseCreditCustomerPayment,
    BaseInventory,
    BasePayment,
    BaseConfig,
    BasePayrol,
    Item,
)
from restaurant.managers import RestaurantPayrolCustomManager
from user.models import User


# Inventory


class MainInventoryItem(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    amount_per_unit = models.PositiveIntegerField(help_text="e.g 4 Plates per 1 Kg")
    price_per_unit = models.PositiveIntegerField(help_text="e.g 1200 per 1 plate")
    objects = Manager()

    def __str__(self) -> str:
        """String representation of object

        Returns:
                str: name
        """
        return self.item.name

    @property
    def unit(self) -> str:
        return self.item.unit.name

    class Meta:
        ordering: List[str] = ["-id"]
        indexes = [
            models.Index(
                fields=[
                    "item",
                    "amount_per_unit",
                    "price_per_unit",
                ]
            )
        ]


class MainInventoryItemRecord(BaseInventory):
    main_inventory_item = models.ForeignKey(MainInventoryItem, on_delete=models.CASCADE)
    threshold = models.IntegerField()

    @property
    def ppu(self) -> int:
        """ppu -> price per unit"""

        return int(self.purchasing_price / self.quantity)

    def __str__(self) -> str:
        """String representation of object

        Returns:
                str: name
        """
        return self.main_inventory_item.item.name

    @property
    def estimate_sales(self) -> int:
        return int(
            self.main_inventory_item.amount_per_unit
            * self.main_inventory_item.price_per_unit
            * self.quantity
        )

    @property
    def estimate_profit(self) -> int:
        return int(self.estimate_sales - self.purchasing_price)

    def send_notification(self, message: str, recipients: List[str]):
        from BeemAfrica import Authorize, SMS
        import requests
        import json

        api_key = "945c064a2f78eaea"
        secret_key = "YmU3ZDJlNzVhMGE3MTE3NDQ3NTJhNTQwN2ZkNWFkMDFiNWQ0ZmRjYjk4ZWU3YjE4MTBmYjdmYjlhYjE0NDdiYw=="

        Authorize(api_key, secret_key)

        try:
            SMS.send_sms(message, recipients, source_addr="RESTAURANT")
        except Exception as e:
            error_name: str = str(e)
            return requests.models.Response(
                json.dumps(error_name),
                status=500,
            )

    @property
    def stock_out_history(self) -> List[Dict]:
        response: List[Dict] = []
        [
            response.append(
                {
                    "history_id": _.id,
                    "quantity_out": f"{_.quantity_out} {_.item_record.main_inventory_item.item.unit.name}",
                    "date_out": _.date_out.__str__(),
                    "created_by": _.created_by.__str__(),
                }
            )
            for _ in self.maininventoryitemrecordstockout_set.select_related(
                "item_record__main_inventory_item__item__unit"
            )
        ]

        return response


class MainInventoryItemRecordTrunk(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    inventory_items = models.ManyToManyField(MainInventoryItemRecord)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    objects = Manager()

    def __str__(self) -> str:
        return "%s Inventory Trunk" % self.item.name

    def get_last_inventory_record(self):  # -> MainInventoryItem
        records = self.inventory_items.select_related("main_inventory_item")[::-1]
        for record in records:
            if record.stock_status == "available" and record.available_quantity > 0:
                return record
            else:
                continue

    @property
    def total_items_added(self) -> int:
        return self.inventory_items.aggregate(total=Sum("quantity"))["total"] or 0

    @property
    def total_items_available(self) -> int:
        return (
            self.inventory_items.aggregate(total=Sum("available_quantity"))["total"]
            or 0
        )

    @property
    def stock_status(self) -> str:
        return "Available" if self.total_items_available else "Unavailable"

    @property
    def total_items_available_repr(self) -> str:
        return str(self.total_items_available) + " " + self.item.unit.name

    def get_stock_in(self) -> List[Dict]:
        stock_in: List[Dict] = []
        for record in self.inventory_items.select_related(
            "main_inventory_item", "main_inventory_item__item__unit"
        ):
            temp_stock_in: Dict = {
                "id": record.id,
                "quantity": str(record.quantity)
                + " "
                + record.main_inventory_item.item.unit.name,
                "purchasing_price": record.purchasing_price,
                # "selling_price_per_item": record.selling_price_per_item,
                "available_items": record.available_quantity,
                "estimated_sales": record.estimate_sales,
                "estimated_profit": record.estimate_profit,
                "stock_status": record.get_stock_status_display(),
                "date_purchased": record.date_purchased.__str__(),
                "date_perished": record.date_perished.__str__(),
            }
            stock_in.append(temp_stock_in)

        return stock_in

    class Meta:
        ordering: Set = ("-id",)
        verbose_name: str = "Main Inventory Item Record Trunk"
        verbose_name_plural: str = "Main Inventory Item Records Trunk"
        indexes = [
            models.Index(
                fields=[
                    "item",
                    "updated_at",
                    "created_at",
                ]
            )
        ]


class MainInventoryItemRecordStockOut(models.Model):
    item_record = models.ForeignKey(MainInventoryItemRecord, on_delete=models.CASCADE)
    quantity_out = models.PositiveIntegerField()
    date_out = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    objects = Manager()

    def get_ppu(self) -> float:
        """get estimatation of selling price per unit of the quantity_out"""

        return float(self.quantity_out * self.item_record.ppu)

    def __str__(self):
        return (
            f"{self.item_record.main_inventory_item.item.name}: {self.quantity_out} Out"
        )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Main Inventory Item Record Stock Out"
        verbose_name_plural = "Main Inventory Item Records Stock Out"
        indexes = [
            models.Index(
                fields=["item_record", "quantity_out", "date_out", "created_by"]
            )
        ]


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

    # description = models.CharField(max_length=255)
    # image = models.FileField(upload_to="menu/images/", null=True, blank=True)
    price = models.IntegerField(db_index=True)


class Additive(BaseConfig):
    """[summary]

    Args:
            models ([type]): [description]
    """

    pass


# Sales


class BaseCustomerOrder(models.Model):
    """Base customer order class"""

    quantity = models.PositiveIntegerField(db_index=True)
    additives = models.ManyToManyField(Additive)
    order_number = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="Leave blank",
        db_index=True,
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    date_created = models.DateTimeField(db_index=True)
    objects = Manager()

    @property
    @abstractmethod
    def total(self) -> float:
        """Returns the total price: i.e sub_menu__price * quantity"""

    class Meta:
        abstract: bool = True
        indexes = [
            models.Index(
                fields=["quantity", "order_number", "date_created", "created_by"]
            )
        ]


class RestaurantCustomerOrder(BaseCustomerOrder):
    """single customer order"""

    sub_menu = models.ForeignKey(Menu, on_delete=models.CASCADE, db_index=True)

    @property
    def total(self) -> int:
        """Returns the total price: i.e sub_menu__price * quantity"""

        return self.quantity * self.sub_menu.price

    def __str__(self) -> str:
        return f"{self.sub_menu.name} Order#{self.order_number}"

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Restaurant Customer Order"
        verbose_name_plural: str = "Restaurant Customer Orders"


class CustomerDish(models.Model):
    """Customer Dish class"""

    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=15, null=True, blank=True)
    orders = models.ManyToManyField(RestaurantCustomerOrder)
    dish_number = models.CharField(
        max_length=255, null=True, blank=True, help_text="Leave blank"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField()
    status = models.CharField(
        max_length=7,
        choices=(
            ("unpaid", "Unpaid"),
            ("partial", "Partially Paid"),
            ("paid", "Fully Paid"),
        ),
    )
    objects = Manager()

    def __str__(self) -> str:
        return f"{self.customer_name}: Dish #{self.dish_number}"

    @property
    def payable_amount(self):
        res_: int = 0
        for order in self.orders.all():
            res_ += order.total
        return res_

    @property
    def paid_amount(self) -> int:
        paid_amount: int = self.customerdishpayment_set.aggregate(
            total=Sum("amount_paid")
        )["total"]

        if paid_amount:
            return paid_amount
        else:
            return 0

    @property
    def remained_amount(self) -> int:
        paid_amount: int = self.get_paid_amount()

        if paid_amount:
            return self.get_total_price - self.get_paid_amount()
        return self.get_total_price

    @property
    def get_total_price(self) -> int:
        res_: int = 0
        for order in self.orders.all():
            res_ += order.total
        return res_

    @property
    def payment_status(self) -> str:
        total_payment = self.get_paid_amount()

        if total_payment and total_payment >= self.get_total_price:
            payment_status: str = "Fully Paid"
        elif total_payment and self.get_total_price <= 0 or not total_payment:
            payment_status: str = "Not Paid"
        else:
            payment_status: str = "Partially Paid"
        return payment_status

    @property
    def dish_detail(self) -> List[Dict]:
        orders_structure: List[Dict] = []
        for order in self.orders.all():
            temp_order: Dict = {
                "order_id": order.id,
                "order_number": order.order_number,
            }
            temp_sub_menu: Dict = {
                "sub_menu_id": order.sub_menu.id,
                "sub_menu_name": order.sub_menu.name,
                "sub_menu_price": order.sub_menu.price,
            }
            temp_sub_menu_additives: List = []
            for additive in order.additives.all():
                temp_additive: Dict = {
                    "additive_id": additive.id,
                    "additive_name": additive.name,
                }
                temp_sub_menu_additives.append(temp_additive)
            temp_sub_menu["sub_menu_additives"] = temp_sub_menu_additives
            temp_order["sub_menu"] = temp_sub_menu
            temp_order["quantity"] = order.quantity
            orders_structure.append(temp_order)

        return orders_structure

    @property
    def get_dish_detail(self) -> List[Dict]:
        res: List[Dict] = []
        [
            res.append(
                {
                    "sub_menu": order.sub_menu.name,
                    "price": order.sub_menu.price,
                    "quantity": order.quantity,
                },
            )
            for order in self.orders.all()
        ]

        return res

    def get_payment_status(self) -> str:
        total_payment = self.get_paid_amount()

        if total_payment and total_payment >= self.get_total_price:
            payment_status: str = "Fully Paid"
        elif total_payment and self.get_total_price <= 0 or not total_payment:
            payment_status: str = "Not Paid"
        else:
            payment_status: str = "Partially Paid"
        return payment_status

    def get_paid_amount(self) -> int:
        paid_amount: int = self.customerdishpayment_set.aggregate(
            total=Sum("amount_paid")
        )["total"]

        if paid_amount:
            return paid_amount
        else:
            return 0

    def get_remained_amount(self) -> int:
        paid_amount: int = self.get_paid_amount()

        if paid_amount:
            return self.get_total_price - self.get_paid_amount()
        return self.get_total_price

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Customer Dish"
        verbose_name_plural: str = "Customer Dishes"
        unique_together: Set[Set[str]] = (("customer_name", "dish_number"),)
        indexes = [
            models.Index(
                fields=[
                    "customer_name",
                    "customer_phone",
                    "dish_number",
                    "date_created",
                    "created_by",
                    "status",
                ]
            )
        ]


class CustomerDishPayment(BasePayment):
    """customer dish payment class"""

    customer_dish = models.ForeignKey(
        CustomerDish, on_delete=models.CASCADE, db_index=True
    )

    def __str__(self) -> str:
        return f"{self.customer_dish}: Payment Status - {self.payment_status}"

    @property
    def get_total_amount_to_pay(self) -> int:
        return self.customer_dish.get_total_price

    @property
    def get_remaining_amount(self) -> int:
        return self.get_total_amount_to_pay - self.amount_paid

    def get_payments_history(self) -> List[Dict]:
        histories: List[Dict] = []
        for val in CreditCustomerDishPaymentHistory.objects.all():
            if val.credit_customer_dish_payment.customer_dish_payment == self:
                histories.append(
                    {
                        "amount_paid": float(val.amount_paid),
                        "date_paid": str(val.date_paid),
                    }
                )

        return histories


class CreditCustomerDishPayment(BaseCreditCustomerPayment):
    customer_dish_payment = models.ForeignKey(
        CustomerDishPayment, on_delete=models.CASCADE, db_index=True
    )

    def get_credit_dish_payable_amount(self) -> float:
        dish_total_price: float = (
            self.customer_dish_payment.customer_dish.get_total_price
        )

        return dish_total_price - self.amount_paid

    class Meta:
        verbose_name: str = "Credit Customer Dish Payment"
        verbose_name_plural: str = "Credit Customer Dish Payments"


class CreditCustomerDishPaymentHistory(models.Model):
    credit_customer_dish_payment = models.ForeignKey(
        CreditCustomerDishPayment, on_delete=models.CASCADE, db_index=True
    )  # Filter all dishes with 'by_credit'=True and 'customer_dish_payment__payment_status' !="paid"
    amount_paid = models.PositiveIntegerField(db_index=True)
    date_paid = models.DateField(db_index=True)
    objects = Manager()

    def __str__(self):
        return self.credit_customer_dish_payment.customer.name

    class Meta:
        ordering: List[str] = ["-id"]
        verbose_name: str = "Credit Customer Dish Payment History"
        verbose_name_plural: str = "Credit Customer Dish Payment Histories"


# Payrolling Management


class RestaurantPayrol(BasePayrol):
    """Restaurant Payrol"""

    # restaurant_payee = models.ForeignKey(
    #     User, related_name="restaurant_payee", on_delete=models.CASCADE
    # )
    name = models.CharField(max_length=128, db_index=True)
    restaurant_payer = models.ForeignKey(
        User, related_name="restaurant_payer", on_delete=models.CASCADE, db_index=True
    )
    objects = RestaurantPayrolCustomManager()

    def __str__(self):
        return f"{self.name} Paid: {self.amount_paid}"

    # def get_monthly_payrolls(self):
    #     start_of_month = datetime.date.today().replace(
    #         day=1
    #     )  # Getting the current month
    #     payemnts_this_month = self.objects.filter(date_paid__gte=start_of_month)
    #     return
