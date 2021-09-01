from rest_framework.exceptions import ValidationError
from core.serializers import InventoryItemSerializer
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from core.models import CreditCustomer, Item
from rest_framework.decorators import action
from restaurant.utils import get_recipients
from django.db.models.aggregates import Sum
from rest_framework import status, viewsets
from restaurant.models import (
    CreditCustomerDishPaymentHistory,
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
    CreditCustomerDishPayment,
    MainInventoryItemRecord,
    RestaurantCustomerOrder,
    CustomerDishPayment,
    MainInventoryItem,
    RestaurantPayrol,
    CustomerDish,
    Additive,
    Menu,
)
from restaurant.serializers import (
    CreditCustomerDishPaymentHistorySerializer,
    MiscellaneousInventoryRecordSerializer,
    MainInventoryItemRecordSerializer,
    RestaurantCustomerOrderSerializer,
    CustomerDishPaymentSerializer,
    MainInventoryItemSerializer,
    RestaurantPayrolSerializer,
    CustomerDishSerializer,
    AdditiveSerializer,
    MenuSerializer,
)
from django.utils import timezone
from typing import Dict, List
from user.models import User
import uuid


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer


class AdditiveViewSet(viewsets.ModelViewSet):
    queryset = Additive.objects.all()
    serializer_class = AdditiveSerializer


class RestaurantInventoryItemView(ListAPIView):
    queryset = Item.objects.filter(item_for__in=["restaurant", "both"])
    serializer_class = InventoryItemSerializer


class MainInventoryItemViewSet(viewsets.ModelViewSet):
    queryset = MainInventoryItem.objects.select_related("item")
    serializer_class = MainInventoryItemSerializer


class MainInventoryItemRecordViewSet(viewsets.ModelViewSet):
    queryset = MainInventoryItemRecord.objects.select_related(
        "main_inventory_item__item", "main_inventory_item__item__unit"
    )
    serializer_class = MainInventoryItemRecordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.data.get("threshold") >= request.data.get("quantity"):
            message: str = "Threshold should be less than quantity"
            return Response({"message": message}, status.HTTP_400_BAD_REQUEST)

        data = self.perform_create(request)
        return Response(data=data, status=status.HTTP_201_CREATED)

    def perform_create(self, request) -> Dict:
        object = MainInventoryItemRecord.objects.create(
            quantity=request.data.get("quantity"),
            purchasing_price=request.data.get("purchasing_price"),
            date_purchased=request.data.get("date_purchased"),
            threshold=request.data.get("threshold"),
            main_inventory_item=MainInventoryItem.objects.get(
                id=request.data.get("main_inventory_item")
            ),
        )
        return {
            "id": object.id,
            "item": object.main_inventory_item.item.name,
            "quantity": object.quantity,
            "threshold": object.threshold,
            "purchasing_price": object.purchasing_price,
            "date_purchased": object.date_purchased,
        }

    def list(self, request, *args, **kwargs):
        response: list = []
        [
            response.append(
                {
                    "id": obj.id,
                    "quantity": f"{obj.quantity} {obj.main_inventory_item.item.unit.name}",
                    "available_quantity": f"{obj.available_quantity} {obj.main_inventory_item.item.unit.name}",
                    "purchasing_price": float(obj.purchasing_price),
                    "date_purchased": obj.date_purchased,
                    "date_perished": obj.date_perished,
                    "stock_status": obj.stock_status.title(),
                    "threshold": f"{obj.threshold} {obj.main_inventory_item.item.unit.name}",
                    "main_inventory_item": str(obj.main_inventory_item),
                    "estimated_sales": obj.estimate_sales,
                    "estimated_profit": obj.estimate_profit,
                    "stock_out_history": obj.stock_out_history,
                }
            )
            for obj in self.queryset
        ]

        return Response(response, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def list_items(self, request, *args, **kwargs):
        names: List = self.get_items_names(self.queryset)
        response: List = []
        data = self.get_response(names, response)

        return Response(data, status.HTTP_200_OK)

    def get_response(self, names, response):
        for index in range(len(names)):
            temp_response: Dict = {}
            temp_response["id"] = index + 1
            temp_response["item_name"] = names[index]
            item_qs, available_quantity, unit = self.get_items_available_quantity_unit(
                names, index
            )
            temp_response["available_quantity"] = str(available_quantity) + " " + unit
            self.get_stock_status(temp_response, available_quantity)
            self.get_records(response, temp_response, item_qs, unit)

        return response

    def get_records(self, response, temp_response, item_qs, unit):
        temp_response["records_items"] = []
        temp_records: Dict = {}
        counter: int = 0
        for item in item_qs:
            temp_records["record_id"] = counter + 1
            temp_records["available_quantity"] = (
                str(item.available_quantity) + " " + unit
            )
            temp_records["received_quantity"] = str(item.quantity) + " " + unit
            temp_records["estimated_sales"] = item.estimate_sales
            temp_records["estimated_profit"] = item.estimate_profit
            temp_records["stock_issued_history"] = item.stock_out_history
            temp_response["records_items"].append(temp_records)
            temp_records: Dict = {}
            counter += 1
        response.append(temp_response)

    def get_stock_status(self, temp_response: dict, available_quantity: int):
        if available_quantity > 0:
            temp_response["stock_status"] = "Available"
        else:
            temp_response["stock_status"] = "Unavailable"

    def get_items_available_quantity_unit(self, names, index):
        item_qs = self.queryset.filter(main_inventory_item__item__name=names[index])
        available_quantity = item_qs.aggregate(
            available_quantity=Sum("available_quantity")
        )["available_quantity"]
        item = item_qs.first()
        unit = item.main_inventory_item.item.unit.name

        return item_qs, available_quantity, unit

    def get_items_names(self, queryset) -> List:
        names: List = []
        for item in queryset:
            name = item.main_inventory_item.item.name
            if name not in names:
                names.append(name)

        return names

    @action(
        detail=False,
        methods=["POST"],
    )
    def stock_out(self, request, *args, **kwargs):
        item_record_name = request.data.get("item_record_name")
        quantity_out = int(request.data.get("quantity_out"))
        if quantity_out == 0:
            return Response(
                {"message": "Quantity out must be greater than 0"},
                status.HTTP_200_OK,
            )
        items = self.filter_items(item_record_name)
        if len(items) == 0:
            return Response(
                {"message": f"{item_record_name} stock is not available"},
                status.HTTP_200_OK,
            )
        elif len(items) == 1:
            item = items[0]
            available_quantity = item.available_quantity
            if available_quantity < quantity_out:
                return Response(
                    {"message": f"{quantity_out} items are not available"},
                    status.HTTP_200_OK,
                )
            self.create_stock_out(request, quantity_out, item)
            self.reduce_availability(quantity_out, item, available_quantity)
            if (
                item.available_quantity <= item.threshold
                and item.available_quantity > 0
            ):
                item.send_notification(
                    message="{} is nearly out of stock. The remained quantity is {} {}".format(
                        item.main_inventory_item.item.name,
                        item.available_quantity,
                        item.main_inventory_item.item.unit.name,
                    ),
                    recipients=get_recipients(),
                )  # mzigo unakaribia kuisha
            if item.available_quantity == 0:
                self.set_unavailable(item)
                item.send_notification(
                    message="{} is out of stock. The remained quantity is {} {}".format(
                        item.main_inventory_item.item.name,
                        item.available_quantity,
                        item.main_inventory_item.item.unit.name,
                    ),
                    recipients=get_recipients(),
                )  # mzigo umeisha
            return Response(
                {
                    "item": str(item),
                    "quantity_out": quantity_out,
                },
                status.HTTP_200_OK,
            )
        else:
            total_available_quantities = (
                self.get_total_available_quantities_for_all_items(items)
            )
            if quantity_out > total_available_quantities:
                return Response(
                    {
                        "message": f"Quantity out must not be greater than {total_available_quantities}"
                    },
                    status.HTTP_200_OK,
                )
            self.issueing_stock(request, quantity_out, items)
            return Response(status.HTTP_200_OK)

    def issueing_stock(self, request, quantity_out, items):
        for stock in items[::-1]:
            if quantity_out == 0:
                break
            if stock.available_quantity > 0:
                if stock.available_quantity < quantity_out:
                    quantity_out -= stock.available_quantity
                    self.create_stock_out(request, stock.available_quantity, stock)
                    stock.stock_status = "unavailable"
                    stock.date_perished = timezone.now()
                    stock.available_quantity = 0
                else:
                    self.create_stock_out(request, quantity_out, stock)
                    stock.available_quantity -= quantity_out
                    quantity_out = 0
                stock.save()

    def get_total_available_quantities_for_all_items(self, items):
        return items.aggregate(total=Sum("available_quantity"))["total"]

    def filter_items(self, item_record_name):  # select_related
        return MainInventoryItemRecord.objects.filter(
            main_inventory_item__item__name=item_record_name, stock_status="available"
        ).select_related("main_inventory_item", "main_inventory_item__item")

    def get_data(self, request):
        item_record_id = int(request.data.get("item_record_id"))
        quantity_out = int(request.data.get("quantity_out"))
        item = MainInventoryItemRecord.objects.get(id=int(item_record_id))
        available_quantity = item.available_quantity
        return quantity_out, item, available_quantity

    def create_stock_out(self, request, quantity_out, item):
        MainInventoryItemRecordStockOut.objects.create(  # Create Stock out history
            item_record=item,
            quantity_out=quantity_out,
            created_by=request.user,
        )

    def reduce_availability(self, quantity_out, item, available_quantity):
        item.available_quantity = available_quantity - quantity_out
        item.save()

    def set_unavailable(self, item):
        item.stock_status = "unavailable"
        item.date_perished = timezone.now()
        item.save()


class MiscellaneousInventoryRecordViewSet(viewsets.ModelViewSet):
    queryset = MiscellaneousInventoryRecord.objects.select_related("item")
    serializer_class = MiscellaneousInventoryRecordSerializer

    @action(
        detail=False,
        methods=["GET"],
    )
    def list_items(self, request, *args, **kwargs):
        names: List = self.get_items_names(self.queryset)
        response: List = []

        data = self.get_response(names, response)

        return Response(data, status.HTTP_200_OK)

    def get_response(self, names: list, response: list) -> Dict:
        for i in range(len(names)):
            temp_resp: Dict = {}
            temp_resp["id"] = i + 1
            temp_resp["name"] = names[i]
            temp_resp["stock_status"] = self.get_stock_status(names[i])
            temp_resp["items"] = []
            qs = self.queryset.filter(item__name=names[i])
            temp: Dict = {}
            self.append_items(temp_resp, qs, temp)

            response.append(temp_resp)

        return response

    def append_items(self, temp_resp: dict, qs, temp: dict):
        counter: int = 0
        for j in qs:
            counter += 1
            temp: Dict = {}
            temp["item_id"] = counter
            temp["purchased_quantity"] = j.quantity
            temp["available_quantity"] = j.available_quantity
            temp["purchasing_price"] = j.purchasing_price
            temp["date_purchased"] = j.date_purchased
            temp_resp["items"].append(temp)

    def get_stock_status(self, item_name: str) -> str:
        qs = self.queryset.filter(item__name=item_name, stock_status="available")
        if qs:
            return "Available"
        return "Unavailable"

    def get_items_names(self, queryset) -> List:
        response: List = []
        for item in queryset:
            if item.item.name not in response:
                response.append(item.item.name)

        return response


class RestaurantCustomerOrderViewSet(viewsets.ModelViewSet):
    queryset = RestaurantCustomerOrder.objects.select_related("sub_menu", "created_by")
    serializer_class = RestaurantCustomerOrderSerializer

    def list(self, request, *args, **kwargs):
        res: dict = []
        [
            res.append(
                {
                    "sub_menu": order.sub_menu.name,
                    "quantity": order.quantity,
                    "order_number": order.order_number,
                    "created_by": order.created_by.username,
                    "date_created": str(order.date_created).split(" ")[0],
                    "time_created": str(order.date_created).split(" ")[1].split(".")[0],
                }
            )
            for order in self.queryset
        ]
        return Response(res, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = RestaurantCustomerOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status.HTTP_400_BAD_REQUEST)

        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request):
        object = RestaurantCustomerOrder.objects.create(
            sub_menu=Menu.objects.get(id=request.data.get("sub_menu")),
            quantity=request.data.get("quantity"),
            order_number=str(uuid.uuid4())[:7],
            created_by=request.user,
        )
        return {
            "id": object.id,
            "sub_menu": object.sub_menu.name,
            "quantity": object.quantity,
            "order_number": object.order_number,
            "created_by": object.created_by.username,
            "date_created": str(object.date_created).split("T")[0],
            "time_created": str(object.date_created).split("T")[1].split(".")[0],
        }


class CustomerDishViewSet(viewsets.ModelViewSet):
    queryset = CustomerDish.objects.prefetch_related("orders")
    serializer_class = CustomerDishSerializer

    def list(self, request, *args, **kwargs):

        return Response(self.get_list(), status=status.HTTP_200_OK)

    def get_list(self) -> List[Dict]:
        res: List[Dict] = []
        [
            res.append(
                {
                    "id": _.id,
                    "customer_name": _.customer_name,
                    "customer_phone": _.customer_phone,
                    "dish_number": _.dish_number,
                    "payable_amount": _.get_total_price,
                    "paid_amount": _.get_paid_amount(),
                    "remained_amount": _.get_remained_amount(),
                    "payment_status": _.get_payment_status(),
                    "orders": self.get_orders(_),
                }
            )
            for _ in self.queryset
        ]

        return res

    def get_additives(self, object):
        res: list = []
        for order in object.orders.all():
            res.append(
                {
                    "order_id": order.id,
                    "additives": order.additives.values("name"),
                }
            )
        return res

    def create(self, request, *args, **kwargs):
        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request) -> dict():
        object = CustomerDish.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            dish_number=str(uuid.uuid4())[:8],
            created_by=request.user,
        )
        self.add_orders(request, object)
        return {
            "customer_name": object.customer_name,
            "customer_phone": object.customer_phone,
            "dish_number": object.dish_number,
            "total_price": object.get_total_price,
            "orders": self.get_orders(object),
            "created_by": object.created_by.username,
            "date_created": object.date_created,
        }

    def add_orders(self, request, object):  # Performance Bottleneck 🕵
        """f(n) = n^2 i.e Quadractic Function."""
        for _ in request.data.get("orders"):
            order = RestaurantCustomerOrder.objects.create(
                sub_menu=Menu.objects.get(id=int(_["sub_menu"])),
                quantity=int(_["quantity"]),
                order_number=str(uuid.uuid4())[:7],
                created_by=request.user,
            )
            for ad_id in _["additives"]:
                order.additives.add(Additive.objects.get(id=int(ad_id["id"])))
            order.save()
            object.orders.add(order)
            object.save()

    def get_orders(self, object):
        orders: list = []

        def _get_additives_by_order(order):
            temp: list = []
            for additive in order.additives.all():
                temp.append(
                    {
                        "additive_id": additive.id,
                        "additive_name": additive.name,
                    }
                )
            return temp

        try:  # Performance Bottleneck 🕵
            for order in object.orders.all():
                self.append_orders(orders, _get_additives_by_order, order)
        except AttributeError:
            for order in object.customer_dish.orders.all():
                self.append_orders(orders, _get_additives_by_order, order)
        return orders

    def append_orders(self, orders, _get_additives_by_order, order):
        orders.append(
            {
                "order_id": order.id,
                "order_number": order.order_number,
                "sub_menu": {
                    "sub_menu_id": order.sub_menu.id,
                    "sub_menu_name": order.sub_menu.name,
                    "sub_menu_price": order.sub_menu.price,
                    "sub_menu_additives": _get_additives_by_order(order),
                },
                "quantity": order.quantity,
            },
        )


class CustomerDishPaymentViewSet(viewsets.ModelViewSet):
    queryset = CustomerDishPayment.objects.select_related(
        "customer_dish", "created_by", "customer_dish__created_by"
    ).prefetch_related("customer_dish__orders")
    serializer_class = CustomerDishPaymentSerializer
    today = timezone.localdate()

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        for qs in self.queryset:
            splitted_date = str(qs.date_paid).split(" ")
            response.append(
                {
                    "id": qs.id,
                    "by_credit": qs.by_credit,
                    "payment_status": qs.payment_status,
                    "payment_method": qs.payment_method,
                    "amount_paid": float(qs.amount_paid),
                    "date_paid": splitted_date[0],
                    "time_paid": splitted_date[1].split(".")[0],
                    "customer_dish": {
                        "dish_id": qs.customer_dish.id,
                        "customer_name": qs.customer_dish.customer_name,
                        "customer_phone": qs.customer_dish.customer_phone,
                        "dish_number": qs.customer_dish.dish_number,
                        "total_price": qs.customer_dish.get_total_price,
                        "orders": CustomerDishViewSet().get_orders(qs),
                    },
                    "created_by": qs.created_by.username,
                }
            )
        return Response(response, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_amount_to_pay(self, request, *args, **kwargs):
        res: list = []
        [
            res.append(
                {
                    "customer_name": ordr.customer_dish.customer_name,
                    "dish_number": ordr.customer_dish.dish_number,
                    "total_payable_amount": ordr.get_total_amount_to_pay,
                    "total_paid_amount": float(ordr.amount_paid),
                    "remained_amount": float(ordr.get_remaining_amount),
                    "payment_status": ordr.payment_status,
                    "payment_method": ordr.payment_method,
                    "dish_detail": ordr.customer_dish.get_dish_detail,
                }
            )
            for ordr in self.queryset
        ]
        return Response(res, status.HTTP_200_OK)

    def get_dish_numbers(self, qs) -> List:
        numbers: List = []
        for dish in qs:
            if dish.customer_dish.dish_number not in numbers:
                numbers.append(dish.customer_dish.dish_number)
        return numbers

    def get_customer_name(self, filtered_qs) -> str:
        first = filtered_qs.first()
        if first:
            return first.customer_dish.customer_name
        else:
            return ""

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_all_paid(self, request, *args, **kwargs):
        res: List = []
        f_qs = self.queryset.filter(payment_status="paid", by_credit=True)
        numbers: List = self.get_dish_numbers(f_qs)
        self.get_dishes_structure(res, numbers, f_qs)

        return Response(res, status.HTTP_200_OK)

    def get_dishes_structure(self, res, numbers, f_qs):
        for number in numbers:
            temp_res: Dict = {}
            filtered_qs = f_qs.filter(customer_dish__dish_number=number)
            temp_res["customer_name"], temp_res["dish_number"] = (
                self.get_customer_name(filtered_qs),
                number,
            )
            self.structure_payments(temp_res, filtered_qs)
            res.append(temp_res)

    def structure_payments(self, temp_res, filtered_qs):
        temp_res["payments_history"] = []
        for qs in filtered_qs:
            temp_pay: Dict = {}
            temp_pay["paid_amount"] = qs.amount_paid
            temp_pay["date_paid"] = str(qs.date_paid).split(" ")[0]
            temp_pay["time_paid"] = str(qs.date_paid).split(" ")[1].split(".")[0]
            temp_res["payments_history"].append(temp_pay)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_all_partial(self, request, *args, **kwargs):
        res: List[Dict] = []
        filtered_qs = self.queryset.filter(payment_status="partial", by_credit=True)
        [
            res.append(
                {
                    "id": qs.id,
                    "customer_name": qs.customer_dish.customer_name,
                    "dish_number": qs.customer_dish.dish_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                    "paid_amount": qs.amount_paid,
                    "remaining_amount": qs.get_remaining_amount,
                    "date_paid": str(qs.date_paid).split(" ")[0],
                    "time_paid": str(qs.date_paid).split(" ")[1].split(".")[0],
                    "dish_detail": qs.customer_dish.get_dish_detail,
                    "payments_history": qs.get_payments_history(),
                }
            )
            for qs in filtered_qs
        ]

        return Response(res, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_all_unpaid(self, request, *args, **kwargs):
        res: List[Dict] = []
        filtered_qs = self.queryset.filter(payment_status="unpaid", by_credit=True)
        [
            res.append(
                {
                    "customer_name": qs.customer_dish.customer_name,
                    "dish_number": qs.customer_dish.dish_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                    "dish_detail": qs.customer_dish.get_dish_detail,
                }
            )
            for qs in filtered_qs
        ]
        return Response(res, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = CustomerDishPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status.HTTP_400_BAD_REQUEST)

        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request):
        by_credit = request.data.get("by_credit")
        amount_paid = float(request.data.get("amount_paid"))
        customer_dish = CustomerDish.objects.get(id=request.data.get("customer_dish"))
        customer = self.get_customer(request)
        if (
            by_credit
            and self.get_advance_amount(customer_dish, amount_paid)
            > customer.credit_limit
        ):
            raise ValidationError(
                "Can't perform this operation. Customer's credit is not enough."
            )
        elif by_credit and self.get_advance_amount(
            customer_dish, amount_paid
        ) > self.get_remained_credit_for_today(customer):
            raise ValidationError(
                "Can't perform this operation. Remained credit for {} is {}".format(
                    customer.name, self.get_remained_credit_for_today(customer)
                )
            )
        object = CustomerDishPayment.objects.create(
            customer_dish=CustomerDish.objects.get(
                id=request.data.get("customer_dish")
            ),
            amount_paid=request.data.get("amount_paid"),
            created_by=request.user,
        )
        self.pay_by_credit(request, by_credit, amount_paid, object)
        self.save_payment_status(object, amount_paid)
        object.save()

        return {
            "customer_dish": str(object.customer_dish),
            "payment_status": object.payment_status,
            "amount_paid": object.amount_paid,
            "date_paid": object.date_paid,
            "created_by": str(object.created_by),
        }

    def get_advance_amount(self, customer_dish, amount_paid) -> float:
        """This is the amount of money customer wants to pay in advance"""

        return customer_dish.get_total_price - amount_paid

    def get_remained_credit_for_today(self, customer) -> float:

        return customer.credit_limit - self.get_today_spend(
            customer
        )  # 20,000 - 15,000 = 5,000

    def get_today_spend(self, customer):
        total_amount: float = 0.0
        qs = self.get_credit_qs(customer)
        for q in qs:
            total_amount += q.get_credit_dish_payable_amount()

        return total_amount  # 15,000

    def get_total_per_day(self, customer) -> float:
        qs = self.get_credit_qs(customer)

        amount_paid: float = qs.aggregate(total=Sum("amount_paid"))["total"]

        return amount_paid

    def get_credit_qs(self, customer):
        return CreditCustomerDishPayment.objects.filter(
            customer=customer, date_created=self.today
        )

    def pay_by_credit(self, request, by_credit, amount_paid, object):
        customer = self.get_customer(request)
        if by_credit and customer:
            object.by_credit = True
            object.save()
            CreditCustomerDishPayment.objects.create(
                customer_dish_payment=object,
                customer=customer,
                amount_paid=amount_paid,
            )
            self._change_customer_details(object, customer)

    def _change_customer_details(self, object, customer):
        customer_dish = object.customer_dish
        customer_dish.customer_name = customer.name
        customer_dish.customer_phone = customer.phone
        customer_dish.save()

    def get_customer(self, request):
        try:
            customer = CreditCustomer.objects.get(
                id=request.data.get("customer_id")
            )
        except CreditCustomer.DoesNotExist:
            customer = None
        return customer

    def save_payment_status(self, object, amount_paid):
        if amount_paid == 0:
            object.payment_status = "unpaid"
        elif amount_paid >= object.get_total_amount_to_pay:
            object.payment_status = "paid"
        else:
            object.payment_status = "partial"
        object.save()


class CreditCustomerDishPaymentHistoryViewSet(viewsets.ModelViewSet):
    queryset = CreditCustomerDishPaymentHistory.objects.select_related(
        "credit_customer_dish_payment__customer_dish_payment__customer_dish"
    )
    serializer_class = CreditCustomerDishPaymentHistorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"message": f"{serializer.errors}"}, status.HTTP_400_BAD_REQUEST
            )
        credit_customer_dish_payment = request.data.get("credit_customer_dish_payment")
        try:
            object = CreditCustomerDishPayment.objects.get(
                id=credit_customer_dish_payment
            )
            if (
                object.customer_dish_payment.payment_status == "paid"
                or object.customer_dish_payment.by_credit is False
            ):
                return Response(
                    {
                        "message": "This order was not taken by credit or is already paid."
                    },
                    status.HTTP_400_BAD_REQUEST,
                )
            serializer.save()
            return Response(
                {"message": "Operation succeed"},
                status.HTTP_201_CREATED,
            )
        except CreditCustomerDishPayment.DoesNotExist:
            return Response(
                {"message": "Credit Dish Chosen does not exists."},
                status.HTTP_400_BAD_REQUEST,
            )


class RestaurantPayrolViewSet(viewsets.ModelViewSet):
    queryset = RestaurantPayrol.objects.select_related(
        "restaurant_payee", "restaurant_payer"
    )
    serializer_class = RestaurantPayrolSerializer

    def update(self, request, pk=None):
        instance = self.get_object()
        restaurant_payee = request.data.get("restaurant_payee")
        amount_paid = request.data.get("amount_paid")
        payment_method = request.data.get("payment_method")
        if restaurant_payee:
            instance.restaurant_payee = User.objects.get(id=int(restaurant_payee))
        if amount_paid:
            instance.amount_paid = amount_paid
        if payment_method:
            instance.payment_method = payment_method
        instance.save()

        return Response({"message": "Operation success"}, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            object = serializer.save(restaurant_payer=request.user)
            data = {
                "payee": object.restaurant_payee.username,
                "payer": object.restaurant_payer.username,
                "amount_paid": object.amount_paid,
                "date_paid": object.date_paid,
                "payment_method": object.payment_method,
            }
        else:
            data = {"message": serializer.errors}
        return Response(data, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_payees(self, request, *args, **kwargs):
        response: list = []
        users = User.objects.filter(
            user_type__in=["restaurant_waiter", "restaurant_cashier"]
        )
        [
            response.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "phone_number": user.mobile_phone,
                    "user_type": user.user_type,
                }
            )
            for user in users
        ]
        return Response(response, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_monthly_payments(self, request, *args, **kwargs):
        response: list = []
        today = timezone.localdate()
        payments_this_month = RestaurantPayrol.objects.filter(
            date_paid__year=today.year,
            date_paid__month=today.month,
        ).select_related("restaurant_payee", "restaurant_payer")
        response: dict = {}
        response["total_paid_amount"] = (
            payments_this_month.aggregate(total=Sum("amount_paid"))["total"] or 0
        )
        payments: list = []
        [
            payments.append(
                {
                    "id": payment.id,
                    "payee": payment.restaurant_payee.username,
                    "payer": payment.restaurant_payer.username,
                    "amount_paid": payment.amount_paid,
                    "date_paid": payment.date_paid,
                    "payment_method": payment.payment_method,
                }
            )
            for payment in payments_this_month
        ]
        response["payments"] = payments
        return Response(response, status.HTTP_200_OK)
