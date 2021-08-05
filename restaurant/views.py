from core.serializers import InventoryItemSerializer
from core.models import CreditCustomer, Item
import datetime
from user.models import User
from django.db.models.aggregates import Sum
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework import permissions, status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from restaurant.models import (
    CreditCustomerDishPayment,
    CreditCustomerDishPaymentHistory,
    CustomerDish,
    CustomerDishPayment,
    MainInventoryItem,
    MainInventoryItemRecord,
    MainInventoryItemRecordStockOut,
    MiscellaneousInventoryRecord,
    Additive,
    Menu,
    RestaurantCustomerOrder,
    RestaurantPayrol,
)
from restaurant.serializers import (
    CreditCustomerDishPaymentHistorySerializer,
    CustomerDishPaymentSerializer,
    CustomerDishSerializer,
    MainInventoryItemRecordSerializer,
    MainInventoryItemSerializer,
    MiscellaneousInventoryRecordSerializer,
    AdditiveSerializer,
    MenuSerializer,
    RestaurantCustomerOrderSerializer,
    RestaurantPayrolSerializer,
)
import uuid


class MenuViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    authentication_classes = [TokenAuthentication]


class AdditiveViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Additive.objects.all()
    serializer_class = AdditiveSerializer
    authentication_classes = [TokenAuthentication]


class RestaurantInventoryItemView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Item.objects.filter(item_for__in=["restaurant", "both"])
    serializer_class = InventoryItemSerializer
    authentication_classes = [TokenAuthentication]


class MainInventoryItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MainInventoryItem.objects.all()
    serializer_class = MainInventoryItemSerializer
    authentication_classes = [TokenAuthentication]


class MainInventoryItemRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MainInventoryItemRecord.objects.select_related("main_inventory_item")
    serializer_class = MainInventoryItemRecordSerializer
    authentication_classes = [TokenAuthentication]

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
            if item.available_quantity <= item.threshold:
                self.send_notification() # mzigo unakaribia kuisha
            if item.available_quantity == 0:
                self.set_unavailable(item)
                self.send_notification() # mzigo umeisha
            return Response(
                {
                    "item": str(item),
                    "quantity_out": quantity_out,
                },
                status.HTTP_200_OK,
            )
        else:
            total_available_quantities = self.get_total_available_quantities_for_all_items(items)
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
        return items.aggregate(
                total=Sum("available_quantity")
            )["total"]

    def filter_items(self, item_record_name):
        return MainInventoryItemRecord.objects.filter(
            main_inventory_item__item__name=item_record_name, stock_status="available"
        )

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

    def send_notification(self):
        print("Sending message notification that stock is nearly out")


class MiscellaneousInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MiscellaneousInventoryRecord.objects.all()
    serializer_class = MiscellaneousInventoryRecordSerializer
    authentication_classes = [TokenAuthentication]


class RestaurantCustomerOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RestaurantCustomerOrder.objects.select_related("sub_menu", "created_by")
    serializer_class = RestaurantCustomerOrderSerializer
    authentication_classes = [TokenAuthentication]

    def list(self, request, *args, **kwargs):
        res: dict = []
        [
            res.append(
                {
                    "sub_menu": order.sub_menu.id,
                    "quantity": order.quantity,
                    "order_number": order.order_number,
                    "created_by": order.created_by.id,
                    "date_created": order.date_created,
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
            "date_created": object.date_created,
            "created_by": object.created_by.username,
        }


class CustomerDishViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerDish.objects.prefetch_related("orders")
    serializer_class = CustomerDishSerializer
    authentication_classes = [TokenAuthentication]

    def list(self, request, *args, **kwargs):

        return Response(self.get_list(), status=status.HTTP_200_OK)

    def get_list(self):
        res: list = []
        [
            res.append(
                {
                    "id": _.id,
                    "customer_name": _.customer_name,
                    "customer_phone": _.customer_phone,
                    "dish_number": _.dish_number,
                    "total_price": _.get_total_price,
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
                sub_menu=Menu.objects.get(id=int(_["menu_id"])),
                quantity=int(_["quantity"]),
                order_number=str(uuid.uuid4)[:7],
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
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerDishPayment.objects.select_related("customer_dish")
    serializer_class = CustomerDishPaymentSerializer
    authentication_classes = [TokenAuthentication]
    today = datetime.datetime.today()

    def list(self, request, *args, **kwargs):
        response: list = []
        for qs in self.queryset:
            response.append(
                {
                    "id": qs.id,
                    "payment_status": qs.payment_status,
                    "payment_method": qs.payment_method,
                    "amount_paid": float(qs.amount_paid),
                    "date_paid": qs.date_paid,
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
                    "dish_detail": ordr.customer_dish.get_dish_detail,
                    "total_payable_amount": ordr.get_total_amount_to_pay,
                    "total_paid_amount": float(ordr.amount_paid),
                    "payment_status": ordr.payment_status,
                    "payment_method": ordr.payment_method,
                }
            )
            for ordr in self.queryset
        ]
        return Response(res, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_all_paid(self, request, *args, **kwargs):
        res: list = []
        filtered_qs = self.queryset.filter(payment_status="paid")
        [
            res.append(
                {
                    "customer_name": qs.customer_dish.customer_name,
                    "dish_number": qs.customer_dish.dish_number,
                    "paid_amount": qs.amount_paid,
                    "date_paid": qs.date_paid,
                }
            )
            for qs in filtered_qs
        ]
        return Response(res, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_all_partial(self, request, *args, **kwargs):
        res: list = []
        filtered_qs = self.queryset.filter(payment_status="partial")
        [
            res.append(
                {
                    "customer_name": qs.customer_dish.customer_name,
                    "dish_number": qs.customer_dish.dish_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                    "paid_amount": qs.amount_paid,
                    "remaining_amount": qs.get_remaining_amount,
                    "date_paid": qs.date_paid,
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
        res: list = []
        filtered_qs = self.queryset.filter(payment_status="unpaid")
        [
            res.append(
                {
                    "customer_name": qs.customer_dish.customer_name,
                    "dish_number": qs.customer_dish.dish_number,
                    "payable_amount": qs.get_total_amount_to_pay,
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
        customer = self.get_customer(request)
        if (
            by_credit and customer and self.get_total_per_day(customer) > 5000
        ):  # 5000 can be changed to any value.
            return Response(
                {
                    "message": f"Can't perform this action. {customer.name} reached credit limit for today."
                }
            )
        object = CustomerDishPayment.objects.create(
            customer_dish=CustomerDish.objects.get(
                id=request.data.get("customer_dish")
            ),
            amount_paid=request.data.get("amount_paid"),
            created_by=request.user,
        )
        self.pay_by_credit(request, by_credit, object)
        self.save_payment_status(request, object)
        object.save()
        return {
            "customer_dish": str(object.customer_dish),
            "payment_status": object.payment_status,
            "amount_paid": object.amount_paid,
            "date_paid": object.date_paid,
            "created_by": str(object.created_by),
        }

    def get_total_per_day(self, customer):
        qs = CreditCustomerDishPayment.objects.filter(
            customer=customer, date_created=self.today
        )
        return qs.aggregate(
            Sum("customer_dish_payment__customer_dish__get_total_price")
        )

    def pay_by_credit(self, request, by_credit, object):
        customer = self.get_customer(request)
        if by_credit and customer:
            object.by_credit = True
            object.save()
            CreditCustomerDishPayment.objects.create(
                customer_dish_payment=object,
                customer=customer,
            )

    def get_customer(self, request):
        try:
            customer = CreditCustomer.objects.get(
                name=request.data.get("customer_name")
            )
        except CreditCustomer.DoesNotExist:
            customer = None
        return customer

    def save_payment_status(self, request, object):
        amount_paid = float(request.data.get("amount_paid"))
        if amount_paid == 0:
            object.payment_status = "unpaid"
        elif amount_paid >= object.get_total_amount_to_pay:
            object.payment_status = "paid"
        else:
            object.payment_status = "partial"


class CreditCustomerDishPaymentHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CreditCustomerDishPaymentHistory.objects.all()
    serializer_class = CreditCustomerDishPaymentHistorySerializer
    authentication_classes = [TokenAuthentication]

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
            if object.payment_status == "paid" and object.by_credit is False:
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
    permission_classes = [permissions.IsAuthenticated]
    queryset = RestaurantPayrol.objects.all()
    serializer_class = RestaurantPayrolSerializer
    authentication_classes = [TokenAuthentication]

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
        today = datetime.date.today()
        payments_this_month = RestaurantPayrol.objects.filter(
            date_paid__year=today.year,
            date_paid__month=today.month,
        ).select_related("restaurant_payee", "restaurant_payer")
        response: dict = {}
        response["total_paid_amount"] = payments_this_month.aggregate(
            total=Sum("amount_paid")
        )["total"]
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
