import uuid
from core.models import Item
from rest_framework.authentication import TokenAuthentication
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from bar.serializers import (
    CustomerOrderRecordPaymentSerializer,
    CustomerOrderRecordSerializer,
    OrderRecordSerializer,
    RegularInventoryRecordSerializer,
    TekilaInventoryRecordSerializer,
)
from bar.models import (
    CustomerRegularOrderRecordPayment,
    CustomerRegularOrderRecord,
    CustomerRegularOrderRecordPayment,
    RegularOrderRecord,
    RegularInventoryRecord,
    TekilaInventoryRecord,
)
from core.utils import get_date_objects, validate_dates


class RegularInventoryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RegularInventoryRecord.objects.all()
    serializer_class = RegularInventoryRecordSerializer
    authentication_classes = [TokenAuthentication]

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
            "selling_price_per_item": instance.selling_price_per_item,
            "estimated_total_cash_after_sale": float(instance.estimate_sales()),
            "estimated_profit_after_sale": float(instance.estimate_profit()),
            "item": instance.item.name,
            "measurement_unit": instance.item.unit.name,
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
    permission_classes = [permissions.IsAuthenticated]
    queryset = TekilaInventoryRecord.objects.all()
    serializer_class = TekilaInventoryRecordSerializer
    authentication_classes = [TokenAuthentication]

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = self.get_res(instance)

        return Response(data=response, status=status.HTTP_200_OK)

    def get_res(self, instance) -> dict():
        return {
            "id": instance.id,
            "quantity": instance.quantity,
            "purchasing_price": float(instance.purchasing_price),
            "date_purchased": instance.date_purchased,
            "date_perished": instance.date_perished,
            "total_shots_per_tekila": instance.total_shots_per_tekila,
            "selling_price_per_shot": instance.selling_price_per_shot,
            "estimated_total_cash_after_sale": float(instance.estimate_sales()),
            "estimated_profit_after_sale": float(instance.estimate_profit()),
            "item": instance.item.name,
            "measurement_unit": instance.item.unit.name,
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
    permission_classes = [permissions.IsAuthenticated]
    queryset = RegularInventoryRecord.objects.filter(stock_status="available")
    authentication_classes = [TokenAuthentication]

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

    # def append_tekila(self, response):
    #     [
    #         response.append(
    #             {
    #                 # "id": tk_item.id,
    #                 "name": tk_item.item.name,
    #                 "selling_price_per_shot": float(tk_item.selling_price_per_shot),
    #                 "items_available": tk_item.available_quantity,
    #                 "stock_status": tk_item.stock_status,
    #                 "item_type": "Tekila",
    #             }
    #         )
    #         for tk_item in self.queryset
    #     ]


class RegularOrderRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RegularOrderRecord.objects.all()
    serializer_class = OrderRecordSerializer
    authentication_classes = [TokenAuthentication]

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
        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status.HTTP_400_BAD_REQUEST)

        data = self.perform_create(request)
        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request):
        object = RegularOrderRecord.objects.create(
            item=Item.objects.get(id=request.data.get("item")),
            quantity=request.data.get("quantity"),
            order_number=str(uuid.uuid4())[:8],
            created_by=request.user,
            date_created=timezone.now(),
        )
        return {
            "id": object.id,
            "item": object.item.name,
            "quantity": object.quantity,
            "order_number": object.order_number,
            "created_by": object.created_by.username,
            "date_created": object.date_created,
        }


class CustomerRegularOrderRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerRegularOrderRecord.objects.all()
    serializer_class = CustomerOrderRecordSerializer
    authentication_classes = [TokenAuthentication]

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = {
            "id": instance.id,
            "customer_name": instance.customer_name,
            "customer_phone": instance.customer_phone,
            "customer_orders_number": instance.customer_orders_number,
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
        self.add_orders(request)
        object.save()
        return {
            "customer_name": object.customer_name,
            "customer_phone": object.customer_phone,
            "dish_number": object.dish_number,
            "orders": object.get_orders_detail,
            "created_by": object.created_by.username,
            "date_created": object.date_created,
        }

    def add_orders(self, request):
        for _ in request.data.get("orders"):
            order = RegularOrderRecord.objects.create(
                item=RegularInventoryRecord.objects.get(id=int(_["item_id"])),
                quantity=_["quantity"],
                order_number=str(uuid.uuid4())[:8],
                created_by=request.user,
            )
            order.save()

    def list(self, request, *args, **kwargs):

        return Response(self.get_list(self.queryset), status.HTTP_200_OK)

    def get_list(self, objects):
        res: list = []
        [
            res.append(
                {
                    "id": _.id,
                    "customer_name": _.customer_name,
                    "customer_phone": _.customer_phone,
                    "customer_orders_number": _.customer_orders_number,
                    "total_price": _.get_total_price,
                    "orders": _.get_orders_detail,
                }
            )
            for _ in objects
        ]
        return res

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
            # Validation: Check if the from_date is less than or equal to the to_date otherwise rise an error
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
        response: list = []
        [
            response.append(
                {
                    "id": order.id,
                    "customer_name": order.customer_name,
                    "customer_phone": order.customer_phone,
                    "customer_orders_number": order.customer_orders_number,
                    "total_price": order.get_total_price,
                    "orders": order.get_orders_detail,
                }
            )
            for order in qs
        ]

        return response


class CustomerRegularOrderRecordPaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerRegularOrderRecordPayment.objects.all()
    serializer_class = CustomerOrderRecordPaymentSerializer
    authentication_classes = [TokenAuthentication]

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
