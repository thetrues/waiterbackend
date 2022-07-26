from typing import Dict, List, NoReturn, Tuple

from django.db.models.aggregates import Sum
from django.db.models.query import QuerySet
from django.utils import timezone
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from core.models import CreditCustomer, Item
from core.serializers import InventoryItemSerializer
from core.utils import orders_number_generator
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
    Menu, MainInventoryItemRecordTrunk,
)
from restaurant.serializers import (
    CreditCustomerDishPaymentHistorySerializer,
    MiscellaneousInventoryRecordSerializer,
    MainInventoryItemRecordSerializer,
    RestaurantCustomerOrderSerializer,
    CustomerDishPaymentSerializer,
    MainInventoryItemSerializer,
    RestaurantPayrolSerializer,
    AdditiveSerializer,
    MenuSerializer, ChangeMenuImageSerializer,
)
from restaurant.utils import get_recipients
from user.models import User


# import uuid


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    menu_image_class = ChangeMenuImageSerializer

    def update(self, request, pk=None):
        instance = self.get_object()
        name = request.data.get("name")
        description = request.data.get("description")
        price = request.data.get("price")
        instance.name = name
        instance.description = description
        instance.price = price
        instance.save()

        return Response({"message": "Operation success"}, status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["PUT"],
    )
    def update_image(self, request, pk=None):
        instance = self.get_object()
        serializer = self.menu_image_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # instance.image = request.data.get("image")
        instance.save()

        return Response({"message": "Operation success"}, status.HTTP_200_OK)


class AdditiveViewSet(viewsets.ModelViewSet):
    queryset = Additive.objects.all()
    serializer_class = AdditiveSerializer


class RestaurantInventoryItemView(ListAPIView):
    queryset = Item.objects.filter(item_for__in=["restaurant", "both"])
    serializer_class = InventoryItemSerializer


class MainInventoryItemViewSet(viewsets.ModelViewSet):
    queryset = MainInventoryItem.objects.select_related("item")
    serializer_class = MainInventoryItemSerializer


class MainInventoryItemRecordTrunkView(viewsets.ModelViewSet):
    """ Main Inventory Item Record Trunk """

    class OutputSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField()
        item = serializers.CharField()
        total_items_available_repr = serializers.CharField()
        stock_status = serializers.CharField()

        class Meta:
            model = MainInventoryItemRecordTrunk
            fields: List[str] = [
                "id",
                "item",
                "total_items_available_repr",
                "stock_status",
            ]

    serializer_class = OutputSerializer

    def get_queryset(self):
        return MainInventoryItemRecordTrunk.objects.select_related("item").prefetch_related(
            "inventory_items").filter(item__item_for="restaurant")

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["GET"],
    )
    def get_stocks_in(self, request, pk=None):
        try:
            trunk = MainInventoryItemRecordTrunk.objects.get(id=pk)
            return Response(data=trunk.get_stock_in(), status=status.HTTP_200_OK)
        except MainInventoryItemRecordTrunk.DoesNotExist:
            return Response(data={"message": "Not Contents"}, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["GET"],
    )
    def get_stocks_out(self, request, pk=None):
        try:
            trunk = MainInventoryItemRecordTrunk.objects.get(id=pk)
            res = []
            for i in trunk.inventory_items.all():
                try:
                    res.append(i.stock_out_history[0])
                except IndexError:
                    continue
            return Response(data=res, status=status.HTTP_200_OK)
        except MainInventoryItemRecordTrunk.DoesNotExist:
            return Response(data={"message": "Not Contents"}, status=status.HTTP_204_NO_CONTENT)


class MainInventoryItemRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MainInventoryItemRecordSerializer

    def get_queryset(self):
        return MainInventoryItemRecord.objects.select_related(
            "main_inventory_item__item", "main_inventory_item__item__unit"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.data.get("threshold") >= request.data.get("quantity"):
            message: str = "Threshold should be less than quantity"
            return Response({"message": message}, status.HTTP_400_BAD_REQUEST)

        data = self.perform_create(request)
        return Response(data=data, status=status.HTTP_201_CREATED)

    def perform_create(self, request) -> Dict:
        object_ = MainInventoryItemRecord.objects.create(
            quantity=request.data.get("quantity"),
            purchasing_price=request.data.get("purchasing_price"),
            date_purchased=request.data.get("date_purchased"),
            threshold=request.data.get("threshold"),
            main_inventory_item=MainInventoryItem.objects.get(
                id=request.data.get("main_inventory_item")
            ),
        )
        return {
            "id": object_.id,
            "item": object_.main_inventory_item.item.name,
            "quantity": object_.quantity,
            "threshold": object_.threshold,
            "purchasing_price": object_.purchasing_price,
            "date_purchased": object_.date_purchased,
        }

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
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
            for obj in self.get_queryset()
        ]

        return Response(response, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def list_items(self, request, *args, **kwargs) -> Response:
        names: List = self.get_items_names(self.get_queryset())
        response: List = []
        data = self.get_response(names, response)

        return Response(data, status.HTTP_200_OK)

    def get_response(self, names, response):
        for index in range(len(names)):
            temp_response: Dict = {"id": index + 1, "item_name": names[index]}
            item_qs, available_quantity, unit = self.get_items_available_quantity_unit(
                names, index
            )
            temp_response["available_quantity"] = str(available_quantity) + " " + unit
            self.get_stock_status(temp_response, available_quantity)
            self.get_records(response, temp_response, item_qs, unit)

        return response

    def get_records(self, response, temp_response, item_qs, unit) -> NoReturn:
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

    def get_stock_status(
            self, temp_response: dict, available_quantity: int
    ) -> NoReturn:
        if available_quantity > 0:
            temp_response["stock_status"] = "Available"
        else:
            temp_response["stock_status"] = "Unavailable"

    def get_items_available_quantity_unit(
            self, names, index
    ) -> Tuple[QuerySet, int, str]:
        item_qs = self.get_queryset().filter(main_inventory_item__item__name=names[index])
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
                    item.threshold >= item.available_quantity > 0
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

    def issueing_stock(self, request, quantity_out, items) -> NoReturn:
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

    def get_total_available_quantities_for_all_items(self, items) -> float:
        return items.aggregate(total=Sum("available_quantity"))["total"]

    def filter_items(self, item_record_name) -> QuerySet:  # select_related
        return MainInventoryItemRecord.objects.filter(
            main_inventory_item__item__name=item_record_name, stock_status="available"
        ).select_related("main_inventory_item", "main_inventory_item__item")

    def get_data(self, request) -> Tuple[int, MainInventoryItemRecord, int]:
        item_record_id: int = int(request.data.get("item_record_id"))
        quantity_out: int = int(request.data.get("quantity_out"))
        item = MainInventoryItemRecord.objects.get(id=int(item_record_id))
        available_quantity: int = item.available_quantity

        return quantity_out, item, available_quantity

    def create_stock_out(self, request, quantity_out, item) -> NoReturn:
        MainInventoryItemRecordStockOut.objects.create(  # Create Stock out history
            item_record=item,
            quantity_out=quantity_out,
            created_by=request.user,
        )

    def reduce_availability(self, quantity_out, item, available_quantity) -> NoReturn:
        item.available_quantity = available_quantity - quantity_out
        item.save()

    def set_unavailable(self, item) -> NoReturn:
        item.stock_status = "unavailable"
        item.date_perished = timezone.now()
        item.save()


class MiscellaneousInventoryRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MiscellaneousInventoryRecordSerializer

    def get_queryset(self):
        return MiscellaneousInventoryRecord.objects.select_related("item")

    @action(
        detail=False,
        methods=["GET"],
    )
    def list_items(self, request, *args, **kwargs):
        names: List = self.get_items_names(self.get_queryset())
        response: List = []

        data = self.get_response(names, response)

        return Response(data, status.HTTP_200_OK)

    def get_response(self, names: list, response: list) -> List:
        for i in range(len(names)):
            temp_resp: Dict = {"id": i + 1, "name": names[i], "stock_status": self.get_stock_status(names[i]),
                               "items": []}
            qs = self.queryset.filter(item__name=names[i])
            temp: Dict = {}
            self.append_items(temp_resp, qs, temp)
            response.append(temp_resp)

        return response

    def append_items(self, temp_resp: dict, qs, temp: dict):
        counter: int = 0
        for j in qs:
            counter += 1
            temp: Dict = {"item_id": counter, "purchased_quantity": j.quantity,
                          "available_quantity": j.available_quantity, "purchasing_price": j.purchasing_price,
                          "date_purchased": j.date_purchased}
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
    serializer_class = RestaurantCustomerOrderSerializer

    def get_queryset(self):
        return RestaurantCustomerOrder.objects.select_related("sub_menu", "created_by")

    def list(self, request, *args, **kwargs):
        res: List[Dict] = []
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
            for order in self.get_queryset()
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
            order_number=orders_number_generator(
                RestaurantCustomerOrder, "order_number"
            ),
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
    """ Customer Dish API """

    today = timezone.localtime()

    class OutputSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField()
        customer_name = serializers.CharField()
        customer_phone = serializers.CharField()
        dish_number = serializers.CharField()
        payable_amount = serializers.IntegerField()
        paid_amount = serializers.IntegerField()
        remained_amount = serializers.IntegerField()
        payment_status = serializers.CharField()
        orders = serializers.ListField(source="dish_detail")

        class Meta:
            model = CustomerDish
            fields = [
                "id",
                "customer_name",
                "customer_phone",
                "dish_number",
                "payable_amount",
                "paid_amount",
                "remained_amount",
                "payment_status",
                "orders",
            ]

    serializer_class = OutputSerializer

    def get_queryset(self):
        return CustomerDish.objects.prefetch_related("orders").filter(
            status__in=["partial", "unpaid", "paid"],
            date_created__date=self.today.date()
        )

    def list(self, request, *args, **kwargs):
        res: List = []
        for q in self.get_queryset():
            if q.status == "paid" and q.date_created.date() != self.today.date():
                pass
            else:
                res.append({
                    "id": q.id,
                    "customer_name": q.customer_name,
                    "customer_phone": q.customer_phone,
                    "dish_number": q.dish_number,
                    "payable_amount": q.payable_amount,
                    "paid_amount": q.paid_amount,
                    "remained_amount": q.remained_amount,
                    "payment_status": q.payment_status,
                    "orders": q.dish_detail,
                })
        return Response(data=res, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request) -> Dict:
        object_ = CustomerDish.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            dish_number=orders_number_generator(CustomerDish, "dish_number"),
            created_by=request.user,
            date_created=self.today,
            status="unpaid"
        )
        self.add_orders(request, object_)
        return {
            "customer_name": object_.customer_name,
            "customer_phone": object_.customer_phone,
            "dish_number": object_.dish_number,
            "total_price": object_.get_total_price,
            "orders": self.get_orders(object_),
            "created_by": object_.created_by.username,
            "date_created": object_.date_created,
        }

    def add_orders(self, request, object_):  # Performance Bottleneck 🕵
        """f(n) = n^2 i.e Quadratic Function."""
        for _ in request.data.get("orders"):
            order = RestaurantCustomerOrder.objects.create(
                sub_menu=Menu.objects.get(id=int(_["sub_menu"])),
                quantity=int(_["quantity"]),
                order_number=orders_number_generator(
                    RestaurantCustomerOrder, "order_number"
                ),
                created_by=request.user,
                date_created=self.today
            )
            for ad_id in _["additives"]:
                order.additives.add(Additive.objects.get(id=int(ad_id["id"])))
            order.save()
            object_.orders.add(order)
            object_.save()

    def get_orders(self, object_):
        orders: List[Dict] = []

        def _get_additives_by_order(order):
            temp: List = []
            for additive in order.additives.all():
                temp.append(
                    {
                        "additive_id": additive.id,
                        "additive_name": additive.name,
                    }
                )
            return temp

        try:  # Performance Bottleneck 🕵
            for order in object_.orders.all():
                self.append_orders(orders, _get_additives_by_order, order)
        except AttributeError:
            for order in object_.customer_dish.orders.all():
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
    """ Customer Dish Payment API """

    serializer_class = CustomerDishPaymentSerializer
    today = timezone.localtime().date()

    def get_queryset(self):
        return CustomerDishPayment.objects.select_related(
            "customer_dish", "created_by", "customer_dish__created_by"
        ).prefetch_related("customer_dish__orders")

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        for qs in self.get_queryset():
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
            for ordr in self.get_queryset()
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
        f_qs = self.get_queryset().filter(payment_status="paid", by_credit=True)
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
        filtered_qs = self.get_queryset().filter(payment_status="partial", by_credit=True)
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
        filtered_qs = self.get_queryset().filter(payment_status="unpaid", by_credit=True)
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

        self.validate_payment_status(customer_dish)

        try:
            object_ = self.get_customer_dish_payment(customer_dish)
            self.change_amount_paid(amount_paid, object_)
            self.change_payment_status(object_, customer_dish)
            self.change_credit_payments(object_)
            # self.change_payment_status(object)

            return {"message": "Success"}

        except CustomerDishPayment.DoesNotExist:
            pass

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
        customer_dish = CustomerDish.objects.get(
            id=request.data.get("customer_dish")
        )
        object_ = CustomerDishPayment.objects.create(
            customer_dish=customer_dish,
            amount_paid=request.data.get("amount_paid"),
            created_by=request.user,
            payment_started=True,
            date_paid=self.today
        )
        self.pay_by_credit(request, by_credit, amount_paid, object_)
        self.save_payment_status(object_, amount_paid, customer_dish)
        object_.save()

        return {
            "customer_dish": str(object_.customer_dish),
            "payment_status": object_.payment_status,
            "amount_paid": object_.amount_paid,
            "date_paid": object_.date_paid,
            "created_by": str(object_.created_by),
        }

    def change_credit_payments(self, object_):
        if object_.by_credit:
            ccdp = self.change_ccdp(object_)

            self.change_ccdph(ccdp)

    def change_ccdph(self, ccdp):
        ccdph = CreditCustomerDishPaymentHistory.objects.filter(
            credit_customer_dish_payment=ccdp
        ).last()
        if ccdph:
            ccdph.amount_paid += ccdp.amount_paid
            ccdph.date_paid = self.today
            ccdph.save()

    def change_ccdp(self, object_):
        ccdp = CreditCustomerDishPayment.objects.filter(
            customer_dish_payment=object_
        ).last()
        ccdp.amount_paid += object_.amount_paid
        ccdp.date_created = self.today
        ccdp.save()
        return ccdp

    def validate_payment_status(self, customer_dish):
        if customer_dish.get_remained_amount() <= 0:
            raise ValidationError("Order is already paid.")

    def get_customer_dish_payment(self, customer_dish):
        return CustomerDishPayment.objects.get(
            payment_started=True,
            customer_dish=customer_dish,
        )

    def change_payment_status(self, object_, customer_dish):
        if object_.amount_paid == 0:
            object_.payment_status = "unpaid"
            customer_dish.status = "unpaid"
        elif object_.amount_paid >= object_.get_total_amount_to_pay:
            object_.payment_status = "paid"
            customer_dish.status = "paid"
        else:
            object_.payment_status = "partial"
            customer_dish.status = "partial"
        object_.save()
        customer_dish.save()

    def change_amount_paid(self, amount_paid, object_):
        object_.amount_paid += amount_paid
        object_.save()

    def get_advance_amount(self, customer_dish, amount_paid) -> int:
        """This is the amount of money customer wants to pay in advance"""

        return customer_dish.get_total_price - amount_paid

    def get_remained_credit_for_today(self, customer) -> int:

        return customer.credit_limit - self.get_today_spend(
            customer
        )  # 20,000 - 15,000 = 5,000

    def get_today_spend(self, customer):
        total_amount: int = 0
        qs = self.get_credit_qs(customer)
        for q in qs:
            total_amount += q.get_credit_dish_payable_amount()

        return total_amount  # 15,000

    def get_total_per_day(self, customer) -> int:
        qs = self.get_credit_qs(customer)

        amount_paid: int = qs.aggregate(total=Sum("amount_paid"))["total"]

        return amount_paid

    def get_credit_qs(self, customer):
        return CreditCustomerDishPayment.objects.filter(
            customer=customer, date_created=self.today
        )

    def pay_by_credit(self, request, by_credit, amount_paid, object_):
        customer = self.get_customer(request)
        if by_credit and customer:
            object_.by_credit = True
            object_.save()
            CreditCustomerDishPayment.objects.create(
                customer_dish_payment=object_,
                customer=customer,
                amount_paid=amount_paid,
                date_created=self.today,
            )
            self._change_customer_details(object_, customer)

    def _change_customer_details(self, object_, customer):
        customer_dish = object_.customer_dish
        customer_dish.customer_name = customer.name
        customer_dish.customer_phone = customer.phone
        customer_dish.save()

    def get_customer(self, request):
        try:
            customer = CreditCustomer.objects.get(id=request.data.get("customer_id"))
        except CreditCustomer.DoesNotExist:
            customer = None
        return customer

    def save_payment_status(self, object_, amount_paid, customer_dish):
        if amount_paid == 0:
            object_.payment_status = "unpaid"
            customer_dish.status = "unpaid"
        elif amount_paid >= object_.get_total_amount_to_pay:
            object_.payment_status = "paid"
            customer_dish.status = "paid"
        else:
            object_.payment_status = "partial"
            customer_dish.status = "partial"
        customer_dish.save()
        object_.save()


class CreditCustomerDishPaymentHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = CreditCustomerDishPaymentHistorySerializer

    def get_queryset(self):
        return CreditCustomerDishPaymentHistory.objects.select_related(
            "credit_customer_dish_payment__customer_dish_payment__customer_dish"
        )

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
    serializer_class = RestaurantPayrolSerializer

    def get_queryset(self):
        return RestaurantPayrol.objects.select_related(
            "restaurant_payer"
        )

    def update(self, request, pk=None):
        instance = self.get_object()
        restaurant_payee = request.data.get("restaurant_payee")
        amount_paid = request.data.get("amount_paid")
        payment_method = request.data.get("payment_method")
        if restaurant_payee:
            instance.name = restaurant_payee
        if amount_paid:
            instance.amount_paid = amount_paid
        if payment_method:
            instance.payment_method = payment_method
        instance.save()

        return Response({"message": "Operation success"}, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            object_ = serializer.save(restaurant_payer=request.user)
            data = {
                "payee": object_.name,
                "payer": object_.restaurant_payer.username,
                "amount_paid": object_.amount_paid,
                "date_paid": object_.date_paid,
                "payment_method": object_.payment_method,
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
        today = timezone.localdate()
        payments_this_month = RestaurantPayrol.objects.filter(
            date_paid__year=today.year,
            date_paid__month=today.month,
        ).select_related("restaurant_payer")
        response: Dict = {}
        response["total_paid_amount"] = (
                payments_this_month.aggregate(total=Sum("amount_paid"))["total"] or 0
        )
        payments: List = []
        [
            payments.append(
                {
                    "id": payment.id,
                    "payee": payment.name,
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
