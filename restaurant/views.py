from rest_framework.authentication import TokenAuthentication
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from user.models import User
from restaurant.models import (
    CustomerDish,
    CustomerDishPayment,
    MainInventoryItem,
    MainInventoryItemRecord,
    MiscellaneousInventoryRecord,
    Additive,
    Menu,
    RestaurantCustomerOrder,
)
from restaurant.serializers import (
    CustomerDishPaymentSerializer,
    CustomerDishSerializer,
    MainInventoryItemRecordSerializer,
    MainInventoryItemSerializer,
    MiscellaneousInventoryRecordSerializer,
    AdditiveSerializer,
    MenuSerializer,
    RestaurantCustomerOrderSerializer,
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


class MainInventoryItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MainInventoryItem.objects.all()
    serializer_class = MainInventoryItemSerializer
    authentication_classes = [TokenAuthentication]


class MainInventoryItemRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MainInventoryItemRecord.objects.all()
    serializer_class = MainInventoryItemRecordSerializer
    authentication_classes = [TokenAuthentication]


class MiscellaneousInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MiscellaneousInventoryRecord.objects.all()
    serializer_class = MiscellaneousInventoryRecordSerializer
    authentication_classes = [TokenAuthentication]


class RestaurantCustomerOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RestaurantCustomerOrder.objects.all()
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
    queryset = CustomerDish.objects.all()
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
        try:
            data = self.perform_create(request)

            return Response(data, status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": e}, status.HTTP_400_BAD_REQUEST)

    def perform_create(self, request) -> dict():
        object = CustomerDish.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            dish_number=str(uuid.uuid4())[:8],
            created_by=request.user,
        )
        self.add_orders(request)
        object.save()
        return {
            "customer_name": object.customer_name,
            "customer_phone": object.customer_phone,
            "dish_number": object.dish_number,
            "orders": self.get_orders(object),
            "created_by": str(object.created_by),
            "date_created": object.date_created,
        }

    def add_orders(self, request):
        for _ in request.data.get("orders"):
            order = RestaurantCustomerOrder.objects.create(
                sub_menu=Menu.objects.get(id=int(_["menu_id"])),
                quantity=_["quantity"],
                order_number=str(uuid.uuid4())[:7],
                created_by=request.user,
            )
            for ad_id in _["additives"]:
                order.additives.add(Additive.objects.get(id=int(ad_id)))
            order.save()

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

        try:
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
    queryset = CustomerDishPayment.objects.all()
    serializer_class = CustomerDishPaymentSerializer
    authentication_classes = [TokenAuthentication]

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
                    # "date_updated": qs.date_updated,
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
        object = CustomerDishPayment.objects.create(
            customer_dish=CustomerDish.objects.get(
                id=request.data.get("customer_dish")
            ),
            amount_paid=request.data.get("amount_paid"),
            created_by=User.objects.get(id=request.data.get("created_by")),
        )
        self.save_payment_status(request, object)
        object.save()
        return {
            "customer_dish": str(object.customer_dish),
            "payment_status": object.payment_status,
            "amount_paid": object.amount_paid,
            "date_paid": object.date_paid,
            "created_by": str(object.created_by),
        }

    def save_payment_status(self, request, object):
        amount_paid = float(request.data.get("amount_paid"))
        if amount_paid == 0:
            object.payment_status = "unpaid"
        elif amount_paid >= object.get_total_amount_to_pay:
            object.payment_status = "paid"
        else:
            object.payment_status = "partial"
