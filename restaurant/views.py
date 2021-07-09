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
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    authentication_classes = (TokenAuthentication,)


class AdditiveViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = Additive.objects.all()
    serializer_class = AdditiveSerializer
    authentication_classes = (TokenAuthentication,)


class MainInventoryItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = MainInventoryItem.objects.all()
    serializer_class = MainInventoryItemSerializer
    authentication_classes = (TokenAuthentication,)


class MainInventoryItemRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = MainInventoryItemRecord.objects.all()
    serializer_class = MainInventoryItemRecordSerializer
    authentication_classes = (TokenAuthentication,)


class MiscellaneousInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = MiscellaneousInventoryRecord.objects.all()
    serializer_class = MiscellaneousInventoryRecordSerializer
    authentication_classes = (TokenAuthentication,)


class RestaurantCustomerOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = RestaurantCustomerOrder.objects.all()
    serializer_class = RestaurantCustomerOrderSerializer
    authentication_classes = (TokenAuthentication,)

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
            created_by=User.objects.get(id=request.data.get("created_by")),
        )
        return {
            "id": object.id,
            "sub_menu": str(object.sub_menu),
            "quantity": object.quantity,
            "order_number": object.order_number,
            "date_created": object.date_created,
            "created_by": str(object.created_by),
        }


class CustomerDishViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = CustomerDish.objects.all()
    serializer_class = CustomerDishSerializer
    authentication_classes = (TokenAuthentication,)

    def create(self, request, *args, **kwargs):
        serializer = CustomerDishSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status.HTTP_400_BAD_REQUEST)

        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request) -> dict():
        object = CustomerDish.objects.create(
            customer_name=request.data.get("customer_name"),
            dish_number=str(uuid.uuid4())[:8],
            created_by=User.objects.get(id=request.data.get("created_by")),
        )
        [
            object.orders.add(RestaurantCustomerOrder.objects.get(id=_))
            for _ in request.data.getlist("orders")
        ]
        object.save()
        orders = self.get_orders(object)
        return {
            "customer_name": object.customer_name,
            "dish_number": object.dish_number,
            "orders": orders,
            "created_by": str(object.created_by),
            "date_created": object.date_created,
        }

    def get_orders(self, object) -> list():
        orders: list = []
        return [
            orders.append(
                {
                    "order_id": order.order_number,
                    "sub_menu": str(order.sub_menu),
                    "quantity": order.quantity,
                },
            )
            for order in object.orders.all()
        ]


class CustomerDishPaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]
    queryset = CustomerDishPayment.objects.all()
    serializer_class = CustomerDishPaymentSerializer
    authentication_classes = (TokenAuthentication,)

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
                    "total_paid_amount": ordr.amount_paid,
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
