from core.utils import get_date_objects, validate_dates
from core.serializers import InventoryItemSerializer
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.db.models.aggregates import Sum
from bar.serializers import (
    TequilaCustomerOrderRecordPaymentSerializer,
    CustomerOrderRecordPaymentSerializer,
    TequilaCustomerOrderRecordSerializer,
    RegularInventoryRecordSerializer,
    TekilaInventoryRecordSerializer,
    CustomerOrderRecordSerializer,
    TequilaOrderRecordSerializer,
    OrderRecordSerializer,
    BarPayrolSerializer,
)
from bar.models import (
    CreditCustomerTequilaOrderRecordPayment,
    CustomerRegularOrderRecordPayment,
    CustomerRegularOrderRecordPayment,
    CustomerTequilaOrderRecordPayment,
    CustomerRegularOrderRecord,
    CustomerTequilaOrderRecord,
    RegularInventoryRecord,
    TekilaInventoryRecord,
    RegularOrderRecord,
    TequilaOrderRecord,
    BarPayrol,
)
from core.models import CreditCustomer, Item
from django.utils import timezone
from typing import Dict, List
from user.models import User
import datetime
import uuid


class BarInventoryItemView(ListAPIView):
    queryset = Item.objects.filter(item_for__in=["bar", "both"])
    serializer_class = InventoryItemSerializer


class RegularInventoryRecordViewSet(viewsets.ModelViewSet):
    queryset = RegularInventoryRecord.objects.select_related("item", "item__unit")
    serializer_class = RegularInventoryRecordSerializer

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = self.get_res(instance)

        return Response(data=response, status=status.HTTP_200_OK)

    def get_res(self, instance):

        return {
            "id": instance.id,
            "quantity": instance.quantity,
            "purchasing_price": float(instance.purchasing_price),
            "date_purchased": instance.date_purchased,
            "total_items": instance.total_items,
            "available_items": instance.available_quantity,
            "threshold": instance.threshold,
            "selling_price_per_item": instance.selling_price_per_item,
            "estimated_total_cash_after_sale": float(instance.estimate_sales()),
            "estimated_profit_after_sale": float(instance.estimate_profit()),
            "item": instance.item.name,
            "measurement_unit": instance.item.unit.name,
            "orders_history": instance.get_orders_history(
                qs=instance.regularorderrecord_set.select_related("created_by")
            ),
        }

    def list(self, request, *args, **kwargs):
        response: list = []
        for record in self.queryset:
            response.append(self.get_res(record))

        return Response(data=response, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_total_cash_after_sale(self, request, pk=None):

        return Response(
            {
                "estimated_total_cash_after_sale": float(
                    self.get_object().estimate_sales()
                )
            },
            status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_profit_after_sale(self, request, pk=None):

        return Response(
            {"estimated_profit_after_sale": float(self.get_object().estimate_profit())},
            status.HTTP_200_OK,
        )


class TekilaInventoryRecordViewSet(viewsets.ModelViewSet):
    queryset = TekilaInventoryRecord.objects.select_related("item", "item__unit")
    serializer_class = TekilaInventoryRecordSerializer

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = self.get_res(instance)

        return Response(data=response, status=status.HTTP_200_OK)

    def get_res(self, instance: TekilaInventoryRecord) -> Dict:
        return {
            "id": instance.id,
            "quantity": instance.quantity,
            "available_quantity": instance.available_quantity,
            "threshold": instance.threshold,
            "purchasing_price": float(instance.purchasing_price),
            "date_purchased": instance.date_purchased,
            "date_perished": instance.date_perished,
            "total_shots_per_tekila": instance.total_shots_per_tekila,
            "selling_price_per_shot": instance.selling_price_per_shot,
            "estimated_total_cash_after_sale": float(instance.estimate_sales()),
            "estimated_profit_after_sale": float(instance.estimate_profit()),
            "item": instance.item.name,
            "measurement_unit": instance.item.unit.name,
            "orders_history": instance.get_orders_history(
                qs=instance.tequilaorderrecord_set.select_related("created_by")
            ),
        }

    def list(self, request, *args, **kwargs):
        response: List = []
        for record in self.queryset:
            response.append(self.get_res(record))

        return Response(data=response, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_total_cash_after_sale(self, request, pk=None):

        return Response(
            {"estimated_total_cash_after_sale": self.get_object().estimate_sales()},
            status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_profit_after_sale(self, request, pk=None):

        return Response(
            {"estimated_profit_after_sale": self.get_object().estimate_profit()},
            status.HTTP_200_OK,
        )


# Sales Management


class BarRegularItemViewSet(viewsets.ModelViewSet):
    queryset = RegularInventoryRecord.objects.filter(
        stock_status="available"
    ).select_related("item", "item__unit")

    def list(self, request, *args, **kwargs):
        response: list = []
        self.append_regular(response)
        return Response(data=response, status=status.HTTP_200_OK)

    def append_regular(self, response):
        [
            response.append(
                {
                    "id": item.id,
                    "name": item.item.name,
                    "selling_price_per_item": float(item.selling_price_per_item),
                    "items_available": item.available_quantity,
                    "stock_status": item.stock_status,
                    "item_type": "Regular",
                }
            )
            for item in self.queryset
        ]


class RegularOrderRecordViewSet(viewsets.ModelViewSet):
    queryset = RegularOrderRecord.objects.select_related(
        "item", "item__item", "created_by"
    )
    serializer_class = OrderRecordSerializer

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        return Response(
            {
                "id": instance.id,
                "item": instance.item.item.name,
                "ordered_quantity": instance.quantity,
                "total_price": instance.total,
                "order_number": instance.order_number,
                "created_by": instance.created_by.username,
                "date_created": instance.date_created,
            },
            status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        response: List = []
        [
            response.append(
                {
                    "id": record.id,
                    "item": record.item.item.name,
                    "ordered_quantity": record.quantity,
                    "total_price": record.total,
                    "order_number": record.order_number,
                    "created_by": record.created_by.username,
                    "date_created": record.date_created,
                }
            )
            for record in self.queryset
        ]
        return Response(response, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request):
        object = RegularOrderRecord.objects.create(
            item=RegularInventoryRecord.objects.get(id=request.data.get("item")),
            quantity=request.data.get("quantity"),
            order_number=str(uuid.uuid4())[:8],
            created_by=request.user,
            date_created=timezone.now(),
        )
        return {
            "id": object.id,
            "item": object.item.item.name,
            "quantity": object.quantity,
            "order_number": object.order_number,
            "created_by": object.created_by.username,
            "date_created": object.date_created,
        }


class CustomerRegularOrderRecordViewSet(viewsets.ModelViewSet):
    queryset = CustomerRegularOrderRecord.objects.select_related(
        "created_by"
    ).prefetch_related("orders")
    serializer_class = CustomerOrderRecordSerializer

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = {
            "id": instance.id,
            "customer_name": instance.customer_name,
            "customer_phone": instance.customer_phone,
            "dish_number": instance.customer_orders_number,
            "total_price": instance.get_total_price,
            "orders": instance.get_orders_detail,
        }
        return Response(response, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        try:
            data = self.perform_create(request)

            return Response(data, status.HTTP_201_CREATED)
        except Exception as e:

            return Response({"message": str(e)}, status.HTTP_400_BAD_REQUEST)

    def perform_create(self, request):
        object = CustomerRegularOrderRecord.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            customer_orders_number=str(uuid.uuid4())[:8],
            created_by=request.user,
        )
        self.add_orders(request, object)
        # object.save()
        return {
            "customer_name": object.customer_name,
            "customer_phone": object.customer_phone,
            "customer_orders_number": object.customer_orders_number,
            "orders": object.get_orders_detail,
            "created_by": object.created_by.username,
            "date_created": object.date_created,
        }

    def add_orders(self, request, object):
        for _ in request.data.get("orders"):
            order = RegularOrderRecord.objects.create(
                item=RegularInventoryRecord.objects.get(id=int(_["menu_id"])),
                quantity=_["quantity"],
                order_number=str(uuid.uuid4())[:8],
                created_by=request.user,
            )
            object.orders.add(order)
        object.save()

    def list(self, request, *args, **kwargs):

        return Response(self.get_list(self.queryset), status.HTTP_200_OK)

    def get_list(self, objects):
        return self.appending(objects)

    @action(
        detail=False,
        methods=["GET"],
    )
    def search(self, request, *args, **kwargs):
        try:
            customer_name = request.data["customer_name"]
            results = CustomerRegularOrderRecord.objects.filter(
                customer_name=customer_name
            )
            return Response(self.get_list(results), status.HTTP_200_OK)
        except KeyError:
            return Response(
                {"message": "Field error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_today_orders(self, request, *args, **kwargs):
        today_date = timezone.localdate()
        qs = self.queryset.filter(date_created__date=today_date)
        response = self.append_orders(qs)

        return Response(response, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_orders_by_dates(self, request, *args, **kwargs):
        try:
            # Convert dates strings to dates objects
            from_date, to_date = get_date_objects(
                request.data["from_date"], request.data["to_date"]
            )
            # Validation: Check if the from_date is less than or equal to the to_date otherwise raise an error
            if validate_dates(from_date, to_date):
                return Response(
                    {"message": "from_date must be less than or equal to to_date"},
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            qs = self.queryset.filter(date_created__date__range=[from_date, to_date])
            response = self.append_orders(qs)
            return Response(response, status.HTTP_200_OK)
        except KeyError:
            return Response(
                {"message": "Invalid dates."}, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def append_orders(self, qs):
        return self.appending(qs)

    def appending(self, objects):
        res: list = []
        [
            res.append(
                {
                    "id": _.id,
                    "customer_name": _.customer_name,
                    "customer_phone": _.customer_phone,
                    "dish_number": _.customer_orders_number,
                    "total_price": _.get_total_price,
                    "orders": _.get_orders_detail,
                }
            )
            for _ in objects
        ]

        return res


class CustomerRegularOrderRecordPaymentViewSet(viewsets.ModelViewSet):
    queryset = CustomerRegularOrderRecordPayment.objects.select_related(
        "customer_order_record", "created_by"
    )
    serializer_class = CustomerOrderRecordPaymentSerializer

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = {
            "id": instance.id,
            "customer_name": instance.customer_order_record.customer_name,
            "customer_phone": instance.customer_order_record.customer_phone,
            "customer_orders_number": instance.customer_order_record.customer_orders_number,
            "payment_status": instance.payment_status,
            "payment_method": instance.payment_method,
            "amount_paid": float(instance.amount_paid),
            "amount_remaining": float(instance.get_remaining_amount),
            "orders": instance.customer_order_record.get_orders_detail,
            "created_by": instance.created_by.username,
            "date_created": instance.date_paid,
        }
        return Response(response, status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        response = self.get_list(self.queryset)
        return Response(response, status.HTTP_200_OK)

    def get_list(self, objects):
        response: list = []
        [
            response.append(
                {
                    "id": payment.id,
                    "customer_name": payment.customer_order_record.customer_name,
                    "customer_phone": payment.customer_order_record.customer_phone,
                    "customer_orders_number": payment.customer_order_record.customer_orders_number,
                    "payment_status": payment.payment_status,
                    "payment_method": payment.payment_method,
                    "amount_paid": float(payment.amount_paid),
                    "amount_remaining": float(payment.get_remaining_amount),
                    "orders": payment.customer_order_record.get_orders_detail,
                    "created_by": payment.created_by.username,
                    "date_created": payment.date_paid,
                }
            )
            for payment in objects
        ]

        return response

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status.HTTP_400_BAD_REQUEST)

        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request):
        # Check if customer is valid to borrow for today
        object = CustomerRegularOrderRecordPayment.objects.create(
            customer_order_record=CustomerRegularOrderRecord.objects.get(
                id=request.data.get("customer_order_record")
            ),
            amount_paid=request.data.get("amount_paid"),
            created_by=request.user,
        )
        self.save_payment_status(request, object)
        object.save()
        return {
            "customer_order_record": str(object),
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
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "paid_amount": float(qs.amount_paid),
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
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
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
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                }
            )
            for qs in filtered_qs
        ]
        return Response(res, status.HTTP_200_OK)


class BarPayrolViewSet(viewsets.ModelViewSet):
    queryset = BarPayrol.objects.select_related("bar_payer", "bar_payee")
    serializer_class = BarPayrolSerializer

    def update(self, request, pk=None):
        instance = self.get_object()
        bar_payee = request.data.get("bar_payee")
        amount_paid = request.data.get("amount_paid")
        payment_method = request.data.get("payment_method")
        if bar_payee:
            instance.bar_payee = User.objects.get(id=int(bar_payee))
        if amount_paid:
            instance.amount_paid = amount_paid
        if payment_method:
            instance.payment_method = payment_method
        instance.save()

        return Response({"message": "Operation success"}, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            object = serializer.save(bar_payer=request.user)
            data = {
                "payee": object.bar_payee.username,
                "payer": object.bar_payer.username,
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
        users = User.objects.filter(user_type__in=["bar_waiter", "bar_cashier"])
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
        today = datetime.date.today()
        payments_this_month = BarPayrol.objects.filter(
            date_paid__year=today.year,
            date_paid__month=today.month,
        )
        response: dict = {}
        response["total_amount_paid"] = (
            payments_this_month.aggregate(total=Sum("amount_paid"))["total"] or 0
        )
        payments: list = []
        [
            payments.append(
                {
                    "id": payment.id,
                    "payee": payment.bar_payee.username,
                    "payer": payment.bar_payer.username,
                    "amount_paid": payment.amount_paid,
                    "date_paid": payment.date_paid,
                    "payment_method": payment.payment_method,
                }
            )
            for payment in payments_this_month
        ]
        response["payments"] = payments
        return Response(response, status.HTTP_200_OK)


## Sale Tequilas


class BarTequilaItemViewSet(viewsets.ModelViewSet):
    queryset = TekilaInventoryRecord.objects.filter(
        stock_status="available"
    ).select_related("item", "item__unit")

    def list(self, request, *args, **kwargs):
        response: list = []
        self.append_regular(response)
        return Response(data=response, status=status.HTTP_200_OK)

    def append_regular(self, response):
        [
            response.append(
                {
                    "id": item.id,
                    "name": item.item.name,
                    "items_available": item.available_quantity,
                    "total_shots_per_tekila": item.total_shots_per_tekila,
                    "selling_price_per_shot": float(item.selling_price_per_shot),
                    "stock_status": item.stock_status,
                    "item_type": "Tequila",
                }
            )
            for item in self.queryset
        ]


class TequilaOrderRecordViewSet(viewsets.ModelViewSet):
    queryset = TequilaOrderRecord.objects.select_related(
        "item", "item__item", "created_by"
    )
    serializer_class = TequilaOrderRecordSerializer

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        return Response(
            {
                "id": instance.id,
                "item": instance.item.item.name,
                "ordered_quantity": instance.quantity,
                "total_price": instance.total,
                "order_number": instance.order_number,
                "created_by": instance.created_by.username,
                "date_created": instance.date_created,
            },
            status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        response: list = []
        [
            response.append(
                {
                    "id": record.id,
                    "item": record.item.item.name,
                    "ordered_quantity": record.quantity,
                    "total_price": record.total,
                    "order_number": record.order_number,
                    "created_by": record.created_by.username,
                    "date_created": record.date_created,
                }
            )
            for record in self.queryset
        ]
        return Response(response, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self.perform_create(request)

        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request):
        object = TequilaOrderRecord.objects.create(
            item=TekilaInventoryRecord.objects.get(id=request.data.get("item")),
            quantity=request.data.get("quantity"),
            order_number=str(uuid.uuid4())[:8],
            created_by=request.user,
            date_created=timezone.now(),
        )
        return {
            "id": object.id,
            "item": object.item.item.name,
            "quantity": object.quantity,
            "order_number": object.order_number,
            "created_by": object.created_by.username,
            "date_created": object.date_created,
        }


class CustomerTequilaOrderRecordViewSet(viewsets.ModelViewSet):
    queryset = CustomerTequilaOrderRecord.objects.select_related(
        "created_by"
    ).prefetch_related("orders")
    serializer_class = TequilaCustomerOrderRecordSerializer

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = {
            "id": instance.id,
            "customer_name": instance.customer_name,
            "customer_phone": instance.customer_phone,
            "dish_number": instance.customer_orders_number,
            "total_price": instance.get_total_price,
            "orders": instance.get_orders_detail,
        }
        return Response(response, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        try:
            data = self.perform_create(request)

            return Response(data, status.HTTP_201_CREATED)
        except Exception as e:

            return Response({"message": str(e)}, status.HTTP_400_BAD_REQUEST)

    def perform_create(self, request):
        object = CustomerTequilaOrderRecord.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            customer_orders_number=str(uuid.uuid4())[:8],
            created_by=request.user,
        )
        self.add_orders(request, object)
        return {
            "customer_name": object.customer_name,
            "customer_phone": object.customer_phone,
            "customer_orders_number": object.customer_orders_number,
            "orders": object.get_orders_detail,
            "created_by": object.created_by.username,
            "date_created": str(object.date_created).split(" ")[0],
            "time_created": str(object.date_created).split(" ")[1].split(".")[0],
        }

    def add_orders(self, request, object):
        for _ in request.data.get("orders"):
            order = TequilaOrderRecord.objects.create(
                item=TekilaInventoryRecord.objects.get(id=int(_["order_id"])),
                quantity=_["quantity"],
                order_number=str(uuid.uuid4())[:8],
                created_by=request.user,
            )
            object.orders.add(order)
        object.save()

    def list(self, request, *args, **kwargs):

        return Response(self.get_list(self.queryset), status.HTTP_200_OK)

    def get_list(self, objects):
        return self.appending(objects)

    @action(
        detail=False,
        methods=["GET"],
    )
    def search(self, request, *args, **kwargs):
        try:
            customer_name = request.data["customer_name"]
            results = (
                CustomerTequilaOrderRecord.objects.filter(customer_name=customer_name)
                .select_related("orders")
                .prefetch_related("orders")
            )
            return Response(self.get_list(results), status.HTTP_200_OK)
        except KeyError:
            return Response(
                {"message": "Field error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_today_orders(self, request, *args, **kwargs):
        todays_date = timezone.localdate()
        qs = self.queryset.filter(date_created__date=todays_date)
        response = self.append_orders(qs)

        return Response(response, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_orders_by_dates(self, request, *args, **kwargs):
        try:
            # Convert dates strings to dates objects
            from_date, to_date = get_date_objects(
                request.data["from_date"], request.data["to_date"]
            )
            # Validation: Check if the from_date is less than or equal to the to_date otherwise raise an error
            if validate_dates(from_date, to_date):
                return Response(
                    {"message": "from_date must be less than or equal to to_date"},
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            qs = self.queryset.filter(date_created__date__range=[from_date, to_date])
            response = self.append_orders(qs)
            return Response(response, status.HTTP_200_OK)
        except KeyError:
            return Response(
                {"message": "Invalid dates."}, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def append_orders(self, qs):

        return self.appending(qs)

    def appending(self, objects):
        res: List = []
        [
            res.append(
                {
                    "id": _.id,
                    "customer_name": _.customer_name,
                    "customer_phone": _.customer_phone,
                    "dish_number": _.customer_orders_number,
                    "total_price": _.get_total_price,
                    "orders": _.get_orders_detail,
                }
            )
            for _ in objects
        ]

        return res


class CustomerTequilaOrderRecordPaymentViewSet(viewsets.ModelViewSet):
    queryset = CustomerTequilaOrderRecordPayment.objects.select_related(
        "customer_order_record", "created_by"
    )
    serializer_class = TequilaCustomerOrderRecordPaymentSerializer

    def retrieve(self, request, pk=None) -> Dict:
        instance = self.get_object()
        response: Dict = {
            "id": instance.id,
            "customer_name": instance.customer_order_record.customer_name,
            "customer_phone": instance.customer_order_record.customer_phone,
            "customer_orders_number": instance.customer_order_record.customer_orders_number,
            "payment_status": instance.payment_status,
            "payment_method": instance.payment_method,
            "amount_paid": float(instance.amount_paid),
            "amount_remaining": float(instance.get_remaining_amount),
            "orders": instance.customer_order_record.get_orders_detail,
            "created_by": instance.created_by.username,
            "date_created": instance.date_paid,
        }
        return Response(response, status.HTTP_200_OK)

    def list(self, request, *args, **kwargs) -> List[Dict]:
        response: Dict = self.get_list(self.queryset)

        return Response(response, status.HTTP_200_OK)

    def get_list(self, objects) -> List[Dict]:
        response: List = []
        [
            response.append(
                {
                    "id": payment.id,
                    "customer_name": payment.customer_order_record.customer_name,
                    "customer_phone": payment.customer_order_record.customer_phone,
                    "customer_orders_number": payment.customer_order_record.customer_orders_number,
                    "payment_status": payment.payment_status,
                    "payment_method": payment.payment_method,
                    "amount_paid": float(payment.amount_paid),
                    "amount_remaining": float(payment.get_remaining_amount),
                    "orders": payment.customer_order_record.get_orders_detail,
                    "created_by": payment.created_by.username,
                    "date_created": payment.date_paid,
                }
            )
            for payment in objects
        ]

        return response

    def create(self, request, *args, **kwargs) -> Dict:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self.perform_create(request)

        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request) -> Dict:
        by_credit = request.data.get("by_credit")
        customer = self.get_customer(request)
        if (
            by_credit and customer and self.get_total_per_day(customer) > 5000
        ):  # 5000 can be changed to any value.
            return Response(
                {
                    "message": f"Can't perform this operation. {customer.name} has reached the credit limit for today."
                }
            )
        object = CustomerTequilaOrderRecordPayment.objects.create(
            customer_order_record=CustomerTequilaOrderRecord.objects.get(
                id=request.data.get("customer_order_record")
            ),
            amount_paid=request.data.get("amount_paid"),
            created_by=request.user,
        )
        self.pay_by_credit(request, by_credit, object)
        self.save_payment_status(request, object)
        object.save()
        return {
            "customer_order_record": str(object),
            "payment_status": object.payment_status,
            "amount_paid": object.amount_paid,
            "date_paid": object.date_paid,
            "created_by": str(object.created_by),
        }

    def pay_by_credit(self, request, by_credit, object):
        customer = self.get_customer(request)
        if by_credit and customer:
            object.by_credit = True
            object.save()
            CreditCustomerTequilaOrderRecordPayment.objects.create(
                record_order_payment_record=object,
                customer=customer,
            )
            self._change_customer_details(object, customer)

    def _change_customer_details(self, object, customer):
        customer_order_record = object.customer_order_record
        customer_order_record.customer_name = customer.name
        customer_order_record.customer_phone = customer.phone
        customer_order_record.save()

    def get_total_per_day(self, customer) -> float:
        qs = CreditCustomerTequilaOrderRecordPayment.objects.filter(
            customer=customer, date_created=self.today
        )
        return qs.aggregate(
            total=Sum(
                "record_order_payment_record__customer_order_record__get_total_price"
            )
        )["total"]

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
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "paid_amount": float(qs.amount_paid),
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
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
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
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                }
            )
            for qs in filtered_qs
        ]
        return Response(res, status.HTTP_200_OK)
