import datetime
from typing import Dict, List

from django.db.models.aggregates import Sum
from django.utils import timezone
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from bar.models import (
    CreditCustomerRegularOrderRecordPayment,
    CreditCustomerRegularOrderRecordPaymentHistory,
    CreditCustomerRegularTequilaOrderRecordPayment,
    CreditCustomerRegularTequilaOrderRecordPaymentHistory,
    CreditCustomerTequilaOrderRecordPayment,
    CreditCustomerTequilaOrderRecordPaymentHistory,
    CustomerRegularOrderRecordPayment,
    CustomerRegularTequilaOrderRecord,
    CustomerRegularTequilaOrderRecordPayment,
    CustomerTequilaOrderRecordPayment,
    CustomerRegularOrderRecord,
    CustomerTequilaOrderRecord,
    RegularInventoryRecord,
    RegularTequilaOrderRecord,
    TekilaInventoryRecord,
    RegularOrderRecord,
    TequilaOrderRecord,
    BarPayrol, RegularInventoryRecordsTrunk, RegularInventoryRecordBroken, TequilaInventoryRecordsTrunk,
    TequilaInventoryRecordBroken,
)
from bar.serializers import (
    CreditCustomerRegularOrderRecordPaymentHistorySerializer,
    CreditCustomerRegularTequilaOrderRecordPaymentHistorySerializer,
    CreditCustomerTequilaOrderRecordPaymentHistorySerializer,
    CustomerRegularTequilaOrderRecordPaymentSerializer,
    RegularTequilaOrderRecordSerializer,
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
from core.models import CreditCustomer, Item
from core.serializers import InventoryItemSerializer
from core.utils import get_date_objects, orders_number_generator, validate_dates
from restaurant.utils import send_notification
from user.models import User


# import uuid


class BarInventoryItemView(ListAPIView):
    serializer_class = InventoryItemSerializer

    def get_queryset(self):
        return Item.objects.filter(item_for__in=["bar", "both"])


class RegularInventoryRecordsTrunkView(viewsets.ModelViewSet):
    """  """

    class OutputSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField()
        item = serializers.CharField()
        total_items_available = serializers.IntegerField()
        stock_status = serializers.CharField()

        class Meta:
            model = RegularInventoryRecordsTrunk
            fields: List[str] = [
                "id",
                "item",
                "main_item_id",
                "total_items_available",
                "stock_status",
            ]

    serializer_class = OutputSerializer

    def get_queryset(self):
        return RegularInventoryRecordsTrunk.objects.select_related("item").prefetch_related(
            "regular_inventory_record").filter(item__tequila=False)

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["GET"]
    )
    def get_orders_history(self, request, pk=None):
        try:
            trunk = RegularInventoryRecordsTrunk.objects.get(id=pk)
            orders_history: List[Dict] = []
            for record in trunk.regular_inventory_record.all():
                for order in record.regularorderrecord_set.values():
                    temp = {
                        "id": order["id"],
                        "item_quantity": order["quantity"],
                        "order_number": order["order_number"],
                        "date_created": str(order["date_created"].date()),
                    }
                    orders_history.append(temp)
            return Response(data=orders_history, status=status.HTTP_200_OK)
        except RegularInventoryRecordsTrunk.DoesNotExist:
            return Response(data={"message": "Not Contents"}, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["GET"],
    )
    def get_stocks_in(self, request, pk=None):
        try:
            trunk = RegularInventoryRecordsTrunk.objects.get(id=pk)
            return Response(data=trunk.get_stock_in(), status=status.HTTP_200_OK)
        except RegularInventoryRecordsTrunk.DoesNotExist:
            return Response(data={"message": "Not Contents"}, status=status.HTTP_204_NO_CONTENT)


class RegularInventoryBrokenCreateView(viewsets.ModelViewSet):
    """ Create Broken Items For Regular Inventory """

    class InputSerializer(serializers.Serializer):
        regular_inventory_record_id = serializers.IntegerField()
        quantity_broken = serializers.IntegerField()

        def validate_quantity_broken(self, quantity_broken) -> int:
            if quantity_broken < 1:
                raise serializers.ValidationError("Quantity must be greater than 0.")
            return quantity_broken

    serializer_class = InputSerializer

    def get_queryset(self):
        return RegularInventoryRecordBroken.objects.select_related("regular_inventory_record")

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        regular_inventory_record_id = serializer.validated_data.get("regular_inventory_record_id")
        quantity_broken = serializer.validated_data.get("quantity_broken")
        regular_inventory_record = RegularInventoryRecord.objects.get(id=regular_inventory_record_id)
        if regular_inventory_record.available_quantity < quantity_broken:
            raise serializers.ValidationError(
                f"Quantity broken must be less than or equal to {regular_inventory_record.available_quantity}")
        RegularInventoryRecordBroken.objects.create(
            regular_inventory_record=regular_inventory_record,
            quantity_broken=quantity_broken
        )

        return Response(status=status.HTTP_201_CREATED)


class TequilaInventoryBrokenCreateView(viewsets.ModelViewSet):
    """ Create Broken Items For Tequila Inventory """

    class InputSerializer(serializers.Serializer):
        tequila_inventory_record_id = serializers.IntegerField()
        quantity_broken = serializers.IntegerField()

        def validate_quantity_broken(self, quantity_broken) -> int:
            if quantity_broken < 1:
                raise serializers.ValidationError("Quantity must be greater than 0.")
            return quantity_broken

    serializer_class = InputSerializer

    def get_queryset(self):
        return TequilaInventoryRecordBroken.objects.select_related("tequila_inventory_record")

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        tequila_inventory_record_id = serializer.validated_data.get("tequila_inventory_record_id")
        quantity_broken = serializer.validated_data.get("quantity_broken")
        tequila_inventory_record = TekilaInventoryRecord.objects.get(id=tequila_inventory_record_id)
        if tequila_inventory_record.available_quantity < quantity_broken:
            raise serializers.ValidationError(
                f"Quantity broken must be less than or equal to {tequila_inventory_record.available_quantity}")
        TequilaInventoryRecordBroken.objects.create(
            tequila_inventory_record=tequila_inventory_record,
            quantity_broken=quantity_broken
        )

        return Response(status=status.HTTP_201_CREATED)


class RegularInventoryRecordViewSet(viewsets.ModelViewSet):
    """  """

    serializer_class = RegularInventoryRecordSerializer

    def get_queryset(self):
        return RegularInventoryRecord.objects.select_related("item", "item__unit")

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: dict = self.get_res(instance)

        return Response(data=response, status=status.HTTP_200_OK)

    def get_res(self, instance):
        return {
            "id": instance.id,
            # "quantity": instance.quantity,
            # "purchasing_price": instance.purchasing_price,
            # "date_purchased": instance.date_purchased,
            # "total_items": instance.total_items,
            # "available_items": instance.available_quantity,
            # "threshold": instance.threshold,
            # "selling_price_per_item": instance.selling_price_per_item,
            # "estimated_total_cash_after_sale": instance.estimate_sales(),
            # "estimated_profit_after_sale": instance.estimate_profit(),
            "item": instance.item.name,
            # "measurement_unit": instance.item.unit.name,
            # "orders_history": instance.get_orders_history(
            #     qs=instance.regularorderrecord_set.select_related("created_by")
            # ),
        }

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        for record in self.get_queryset():
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
    serializer_class = TekilaInventoryRecordSerializer

    def get_queryset(self):
        return TekilaInventoryRecord.objects.select_related("item", "item__unit")

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
            "purchasing_price": instance.purchasing_price,
            "date_purchased": instance.date_purchased,
            "date_perished": instance.date_perished,
            "total_shots_per_tekila": instance.total_shots_per_tekila,
            "selling_price_per_shot": instance.selling_price_per_shot,
            "estimated_total_cash_after_sale": instance.estimate_sales(),
            "estimated_profit_after_sale": instance.estimate_profit(),
            "item": instance.item.name,
            "measurement_unit": instance.item.unit.name,
            "orders_history": instance.get_orders_history(
                qs=instance.tequilaorderrecord_set.select_related("created_by")
            ),
        }

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        for record in self.get_queryset():
            response.append(self.get_res(record))

        return Response(data=response, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_total_cash_after_sale(self, request, pk=None) -> Response:
        return Response(
            {"estimated_total_cash_after_sale": self.get_object().estimate_sales()},
            status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["GET"],
    )
    def estimate_profit_after_sale(self, request, pk=None) -> Response:
        return Response(
            {"estimated_profit_after_sale": self.get_object().estimate_profit()},
            status.HTTP_200_OK,
        )


class TequilaInventoryRecordsTrunkView(viewsets.ModelViewSet):
    """ Tequila Inventory Records Trunk View """

    class OutputSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField()
        item = serializers.CharField()
        total_items_available = serializers.IntegerField()
        stock_status = serializers.CharField()

        class Meta:
            model = TequilaInventoryRecordsTrunk
            fields: List[str] = [
                "id",
                "item",
                "main_item_id",
                "total_items_available",
                "stock_status",
            ]

    serializer_class = OutputSerializer

    def get_queryset(self):
        return TequilaInventoryRecordsTrunk.objects.select_related("item").prefetch_related(
            "tequila_inventory_record").filter(item__tequila=True)

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["GET"]
    )
    def get_orders_history(self, request, pk=None):
        try:
            trunk = TequilaInventoryRecordsTrunk.objects.get(id=pk)
            orders_history: List[Dict] = []
            for record in trunk.tequila_inventory_record.all():
                for order in record.tequilaorderrecord_set.values():
                    temp = {
                        "id": order["id"],
                        "shots_quantity": order["quantity"],
                        "order_number": order["order_number"],
                        "date_created": str(order["date_created"].date()),
                    }
                    orders_history.append(temp)
            return Response(data=orders_history, status=status.HTTP_200_OK)
        except TequilaInventoryRecordsTrunk.DoesNotExist:
            return Response(data={"message": "Not Contents"}, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["GET"],
    )
    def get_stocks_in(self, request, pk=None):
        try:
            trunk = TequilaInventoryRecordsTrunk.objects.get(id=pk)
            return Response(data=trunk.get_stock_in(), status=status.HTTP_200_OK)
        except TequilaInventoryRecordsTrunk.DoesNotExist:
            return Response(data={"message": "Not Contents"}, status=status.HTTP_204_NO_CONTENT)


# Sales Management


class BarRegularItemViewSet(viewsets.ModelViewSet):
    # queryset = RegularInventoryRecord.objects.all()
    serializer_class = RegularInventoryRecordSerializer

    def get_queryset(self):
        return RegularInventoryRecordsTrunk.objects.select_related("item", "item__unit").prefetch_related(
            "regular_inventory_record")

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        self.append_regular(response)
        return Response(data=response, status=status.HTTP_200_OK)

    def append_regular(self, response: List[Dict]):
        for item in self.get_queryset():
            if item.get_items_to_sale():
                response.append(item.get_items_to_sale())
        return response


class RegularOrderRecordViewSet(viewsets.ModelViewSet):
    serializer_class = OrderRecordSerializer

    def get_queryset(self):
        return RegularOrderRecord.objects.select_related(
            "item", "item__item", "created_by"
        )

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
                "date_created": str(instance.date_created).split(" ")[0],
                "time_created": str(instance.date_created).split(" ")[1].split(".")[0],
            },
            status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        [
            response.append(
                {
                    "id": record.id,
                    "item": record.item.item.name,
                    "ordered_quantity": record.quantity,
                    "total_price": record.total,
                    "order_number": record.order_number,
                    "created_by": record.created_by.username,
                    "date_created": str(record.date_created).split(" ")[0],
                    "time_created": str(record.date_created)
                        .split(" ")[1]
                        .split(".")[0],
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
        object_ = RegularOrderRecord.objects.create(
            item=RegularInventoryRecord.objects.get(id=request.data.get("item")),
            quantity=request.data.get("quantity"),
            order_number=str(
                orders_number_generator(RegularOrderRecord, "order_number")
            ),
            created_by=request.user,
            date_created=timezone.now(),
        )
        return {
            "id": object_.id,
            "item": object_.item.item.name,
            "quantity": object_.quantity,
            "order_number": object_.order_number,
            "created_by": object_.created_by.username,
            "date_created": object_.date_created,
        }


class CustomerRegularOrderRecordViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerOrderRecordSerializer

    def get_queryset(self):
        return CustomerRegularOrderRecord.objects.select_related(
            "created_by"
        ).prefetch_related("orders")

    def retrieve(self, request, pk=None) -> Response:
        instance = self.get_object()
        response: Dict = {
            "id": instance.id,
            "customer_name": instance.customer_name,
            "customer_phone": instance.customer_phone,
            "dish_number": instance.customer_orders_number,
            "payable_amount": instance.get_total_price,
            "paid_amount": instance.get_paid_amount(),
            "remained_amount": instance.get_remained_amount(),
            "payment_status": instance.get_payment_status(),
            "orders": instance.get_orders_detail,
        }
        return Response(response, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs) -> Response:
        try:
            data = self.perform_create(request)

            return Response(data, status.HTTP_201_CREATED)

        except Exception as e:

            return Response({"message": str(e)}, status.HTTP_400_BAD_REQUEST)

    def perform_create(self, request) -> Dict:
        object_ = CustomerRegularOrderRecord.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            customer_orders_number=str(
                orders_number_generator(
                    CustomerRegularOrderRecord, "customer_orders_number"
                )
            ),
            created_by=request.user,
        )
        self.add_orders(request, object_)
        return {
            "customer_name": object_.customer_name,
            "customer_phone": object_.customer_phone,
            "customer_orders_number": object_.customer_orders_number,
            "orders": object_.get_orders_detail,
            "created_by": object_.created_by.username,
            "date_created": str(object_.date_created).split(" ")[0],
            "time_created": str(object_.date_created).split(" ")[1].split(".")[0],
        }

    def add_orders(self, request, object_):
        for _ in request.data.get("orders"):
            order = RegularOrderRecord.objects.create(
                item=RegularInventoryRecord.objects.get(id=int(_["menu_id"])),
                quantity=_["quantity"],
                order_number=str(
                    orders_number_generator(RegularOrderRecord, "order_number")
                ),
                created_by=request.user,
            )
            object_.orders.add(order)
        object_.save()

    def list(self, request, *args, **kwargs) -> Response:

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
        res: List[Dict] = []
        [
            res.append(
                {
                    "id": _.id,
                    "customer_name": _.customer_name,
                    "customer_phone": _.customer_phone,
                    "dish_number": _.customer_orders_number,
                    "payable_amount": _.get_total_price,
                    "paid_amount": _.get_paid_amount(),
                    "remained_amount": _.get_remained_amount(),
                    "payment_status": _.get_payment_status(),
                    "orders": _.get_orders_detail,
                }
            )
            for _ in objects
        ]

        return res


class CustomerRegularOrderRecordPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerOrderRecordPaymentSerializer
    today = timezone.localdate()

    def get_queryset(self):
        return CustomerRegularOrderRecordPayment.objects.select_related(
            "customer_order_record", "created_by"
        )

    def retrieve(self, request, pk=None):
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
            "date_paid": str(instance.date_paid).split(" ")[0],
            "time_paid": str(instance.date_paid).split(" ")[1].split(".")[0],
        }
        return Response(response, status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        response: List[Dict] = self.get_list(self.queryset)

        return Response(response, status.HTTP_200_OK)

    def get_list(self, objects):
        response: List[Dict] = []
        [
            response.append(
                {
                    "id": payment.id,
                    "by_credit": payment.by_credit,
                    "customer_name": payment.customer_order_record.customer_name,
                    "customer_phone": payment.customer_order_record.customer_phone,
                    "customer_orders_number": payment.customer_order_record.customer_orders_number,
                    "payment_status": payment.payment_status,
                    "payment_method": payment.payment_method,
                    "payable_amount": float(payment.get_total_amount_to_pay),
                    "paid_amount": float(payment.amount_paid),
                    "remained_amount": float(payment.get_remaining_amount),
                    "orders": payment.customer_order_record.get_orders_detail,
                    "created_by": payment.created_by.username,
                    "date_paid": str(payment.date_paid).split(" ")[0],
                    "time_paid": str(payment.date_paid).split(" ")[1].split(".")[0],
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
        by_credit = request.data.get("by_credit")
        amount_paid = float(request.data.get("amount_paid"))
        customer = self.get_customer(request)
        customer_regular_order_record = CustomerRegularOrderRecord.objects.get(
            id=request.data.get("customer_order_record")
        )

        if customer_regular_order_record.get_remained_amount() <= 0:
            raise ValidationError("Order is already paid.")

        try:
            object_ = CustomerRegularOrderRecordPayment.objects.get(
                payment_started=True,
                customer_order_record=customer_regular_order_record,
            )
            object_.amount_paid += amount_paid
            object_.save()
            if object_.amount_paid >= object_.get_total_amount_to_pay:
                object_.payment_status = "paid"
            elif object_.amount_paid <= object_.get_total_amount_to_pay:
                object_.payment_status = "partial"
            else:
                object_.payment_status = "unpaid"
            object_.save()

            return Response(status.HTTP_200_OK)

        except CustomerRegularOrderRecordPayment.DoesNotExist:
            pass

        if (
                by_credit
                and self.get_advance_amount(customer_regular_order_record, amount_paid)
                > customer.credit_limit
        ):
            raise ValidationError(
                "Can't perform this operation. Customer's credit is not enough."
            )

        elif by_credit and self.get_advance_amount(
                customer_regular_order_record, amount_paid
        ) > self.get_remained_credit_for_today(customer):
            raise ValidationError(
                "Can't perform this operation. Remained credit for {} is {}".format(
                    customer.name, self.get_remained_credit_for_today(customer)
                )
            )

        object_ = CustomerRegularOrderRecordPayment.objects.create(
            customer_order_record=customer_regular_order_record,
            amount_paid=amount_paid,
            created_by=request.user,
            payment_started=True,
        )

        self.pay_by_credit(request, by_credit, amount_paid, object_)
        self.save_payment_status(request, object_)

        object_.save()
        return {
            "customer_order_record": str(object_),
            "payment_status": object_.payment_status,
            "amount_paid": object_.amount_paid,
            "date_paid": object_.date_paid,
            "created_by": str(object_.created_by),
        }

    def pay_by_credit(self, request, by_credit, amount_paid, object_):
        customer = self.get_customer(request)
        if by_credit and customer:
            object_.by_credit = True
            object_.save()
            CreditCustomerRegularOrderRecordPayment.objects.create(
                record_order_payment_record=object_,
                customer=customer,
                amount_paid=amount_paid,
                date_created=timezone.localdate(),
            )
            self._change_customer_details(object_, customer)

    def _change_customer_details(self, object_, customer):
        customer_regular_order_record = object_.customer_order_record
        customer_regular_order_record.customer_name = customer.name
        customer_regular_order_record.customer_phone = customer.phone
        customer_regular_order_record.save()

    def save_payment_status(self, request, object_):
        amount_paid = float(request.data.get("amount_paid"))
        if amount_paid == 0:
            object_.payment_status = "unpaid"
        elif amount_paid >= object_.get_total_amount_to_pay:
            object_.payment_status = "paid"
        else:
            object_.payment_status = "partial"

    def get_customer(self, request):
        try:
            customer = CreditCustomer.objects.get(id=request.data.get("customer_id"))
        except CreditCustomer.DoesNotExist:
            customer = None
        return customer

    def get_remained_credit_for_today(self, customer) -> float:

        return customer.credit_limit - self.get_today_spend(
            customer
        )  # 20,000 - 15,000 = 5,000

    def get_today_spend(self, customer) -> float:
        total_amount: float = 0.0
        qs = self.get_credit_qs(customer)
        for q in qs:
            total_amount += q.get_credit_dish_payable_amount()

        return total_amount  # 15,000.0

    def get_credit_qs(self, customer):
        return CreditCustomerRegularOrderRecordPayment.objects.filter(
            customer=customer, date_created=self.today
        )

    def get_advance_amount(self, customer_regular_order_record, amount_paid) -> float:
        """This is the amount of money customer wants to pay in advance"""

        return customer_regular_order_record.get_total_price - amount_paid

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_all_paid(self, request, *args, **kwargs):
        res: List[Dict] = []
        filtered_qs = self.get_queryset().filter(payment_status="paid")
        [
            res.append(
                {
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "paid_amount": float(qs.amount_paid),
                    "date_paid": str(qs.date_paid).split(" ")[0],
                    "time_paid": str(qs.date_paid).split(" ")[1].split(".")[0],
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
        res: List[Dict] = []
        filtered_qs = self.get_queryset().filter(payment_status="partial")
        [
            res.append(
                {
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                    "paid_amount": qs.amount_paid,
                    "remaining_amount": qs.get_remaining_amount,
                    "date_paid": str(qs.date_paid).split(" ")[0],
                    "time_paid": str(qs.date_paid).split(" ")[1].split(".")[0],
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
        filtered_qs = self.get_queryset().filter(payment_status="unpaid")
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


# Sales Changes Starts


class RegularTequilaOrderRecordViewSet(viewsets.ModelViewSet):
    """  """

    today = timezone.localtime()

    serializer_class = RegularTequilaOrderRecordSerializer

    def get_queryset(self):
        return RegularTequilaOrderRecord.objects.select_related(
            "created_by"
        ).prefetch_related("regular_items", "tequila_items")

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        return Response(
            {
                "id": instance.id,
                "order_number": instance.order_number,
                "total_price": instance.get_total_price(),
                "regular_orders": instance.get_regular_items_details(),
                "tequila_orders": instance.get_tequila_items_details(),
                "created_by": instance.created_by.username,
                "date_created": str(instance.date_created).split(" ")[0],
                "time_created": str(instance.date_created).split(" ")[1].split(".")[0],
            },
            status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        [
            response.append(
                {
                    "id": record.id,
                    "order_number": record.order_number,
                    "total_price": record.get_total_price(),
                    "regular_orders": record.get_regular_items_details(),
                    "tequila_orders": record.get_tequila_items_details(),
                    "created_by": record.created_by.username,
                    "date_created": str(record.date_created).split(" ")[0],
                    "time_created": str(record.date_created)
                        .split(" ")[1]
                        .split(".")[0],
                }
            )
            for record in self.get_queryset()
        ]
        return Response(response, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = self.perform_create(request)

        return Response(data=data, status=status.HTTP_201_CREATED)

    def perform_create(self, request):
        orders = request.data.get("orders")
        # For Regular Orders
        for regular_order in orders["regular_orders"]:
            try:
                regular_inv_record = RegularInventoryRecord.objects.get(id=regular_order["item_id"])
                item = regular_inv_record.item
            except RegularInventoryRecord.DoesNotExist:
                raise serializers.ValidationError({"message": "No inventory records found."})
            try:
                trunk = RegularInventoryRecordsTrunk.objects.get(item=item)
            except RegularInventoryRecordsTrunk.DoesNotExist:
                raise serializers.ValidationError({"message": "No inventory records found."})
            if regular_order["quantity"] > trunk.total_items_available:
                raise serializers.ValidationError(
                    {"message": f"{item.name} quantity must not exceed {trunk.total_items_available}"})

        # For Tequila Orders
        for tequila_order in orders["tequila_orders"]:
            try:
                tequila_inv_record = TekilaInventoryRecord.objects.get(id=tequila_order["item_id"])
                item = tequila_inv_record.item
            except TekilaInventoryRecord.DoesNotExist:
                raise serializers.ValidationError({"message": "Something went wrong."})
            try:
                trunk = TequilaInventoryRecordsTrunk.objects.get(item=item)
            except TequilaInventoryRecordsTrunk.DoesNotExist:
                raise serializers.ValidationError({"message": "Something went wrong."})
            if tequila_order["quantity"] > trunk.total_items_available:
                raise serializers.ValidationError(
                    {"message": f"{item.name} quantity must not exceed {trunk.total_items_available}"})

        object_ = RegularTequilaOrderRecord.objects.create(
            order_number=str(
                orders_number_generator(RegularTequilaOrderRecord, "order_number")
            ),
            created_by=request.user,
            date_created=self.today,
        )

        self.create_regular_orders(request, object_, orders["regular_orders"])
        self.create_tequila_orders(request, object_, orders["tequila_orders"])
        object_.save()

        self.create_customer_order(request, object_)

        return {"message": "Order created."}

    def create_customer_order(self, request, object_):
        CustomerRegularTequilaOrderRecord.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            regular_tequila_order_record=object_,
            customer_orders_number=str(
                orders_number_generator(
                    CustomerRegularTequilaOrderRecord, "customer_orders_number"
                )
            ),
            created_by=request.user,
            date_created=self.today
        )

    def create_tequila_orders(self, request, object_, tequila_orders):
        for tequila_order in tequila_orders:
            required_qty = tequila_order["quantity"]
            tequila_inv_record = TekilaInventoryRecord.objects.get(id=tequila_order["item_id"])
            item = tequila_inv_record.item
            trunk = TequilaInventoryRecordsTrunk.objects.get(item=item)

            flag = True  # Loop controller
            while flag:
                last_tequila_inv_record = trunk.get_last_inventory_record()
                res = last_tequila_inv_record.available_quantity - required_qty  # 2 - 8 = -6
                if res < 0:
                    last_tequila_inv_record.available_quantity = 0
                    last_tequila_inv_record.stock_status = "unavailable"
                    last_tequila_inv_record.date_perished = timezone.now()
                    last_tequila_inv_record.save()
                    required_qty = - res  # turn -ve to +ve
                elif res == 0:
                    last_tequila_inv_record.available_quantity = 0
                    last_tequila_inv_record.stock_status = "unavailable"
                    last_tequila_inv_record.date_perished = timezone.now()
                    last_tequila_inv_record.save()
                    flag = False
                else:
                    last_tequila_inv_record.available_quantity -= required_qty
                    last_tequila_inv_record.save()
                    flag = False
            trunk.updated_at = timezone.now()
            trunk.save()

            tequila_order_object = TequilaOrderRecord.objects.create(
                item=TekilaInventoryRecord.objects.get(id=tequila_order["item_id"]),
                quantity=tequila_order["quantity"],
                order_number=str(
                    orders_number_generator(RegularOrderRecord, "order_number")
                ),
                created_by=request.user,
                date_created=timezone.now(),
            )
            object_.tequila_items.add(tequila_order_object)

    def create_regular_orders(self, request, object_, regular_orders):
        for regular_order in regular_orders:
            required_qty = regular_order["quantity"]
            regular_inv_record = RegularInventoryRecord.objects.get(id=regular_order["item_id"])
            item = regular_inv_record.item
            trunk = RegularInventoryRecordsTrunk.objects.get(item=item)

            flag = True  # Loop controller
            while flag:
                last_regular_inv_record = trunk.get_last_inventory_record()
                res = last_regular_inv_record.available_quantity - required_qty  # 2 - 8 = -6
                if res < 0:
                    last_regular_inv_record.available_quantity = 0
                    last_regular_inv_record.stock_status = "unavailable"
                    last_regular_inv_record.save()
                    required_qty = - res  # turn -ve to +ve
                elif res == 0:
                    last_regular_inv_record.available_quantity = 0
                    last_regular_inv_record.stock_status = "unavailable"
                    last_regular_inv_record.save()
                    flag = False
                else:
                    last_regular_inv_record.available_quantity -= required_qty
                    last_regular_inv_record.save()
                    flag = False
            trunk.updated_at = timezone.now()
            trunk.save()

            regular_order_object = RegularOrderRecord.objects.create(
                item=RegularInventoryRecord.objects.get(id=regular_order["item_id"]),
                quantity=regular_order["quantity"],
                order_number=str(
                    orders_number_generator(RegularOrderRecord, "order_number")
                ),
                created_by=request.user,
                date_created=timezone.now(),
            )
            object_.regular_items.add(regular_order_object)

    @action(
        detail=False,
        methods=["POST"],
    )
    def add_order(self, request, *args, **kwargs):
        try:
            object_ = RegularTequilaOrderRecord.objects.get(
                id=request.data.get("customer_order_id")
            )
        except RegularTequilaOrderRecord.DoesNotExist:
            return Response(
                {"error": "Order selected does not exist"}, status.HTTP_200_OK
            )

        orders = request.data.get("orders")
        self.add_regular_orders(request, orders, object_)
        self.add_tequila_orders(request, orders, object_)
        self.change_payment_status(object_)

        return Response({"message": "Order added"}, status.HTTP_200_OK)

    def change_payment_status(self, object_):
        crtorp = CustomerRegularTequilaOrderRecordPayment.objects.get(
            customer_regular_tequila_order_record__regular_tequila_order_record=object_
        )
        if crtorp.payment_started:
            crtorp.payment_status = "partial"
            crtorp.save()

    @action(
        detail=False,
        methods=["POST"],
    )
    def remove_order(self, request, *args, **kwargs):
        try:
            object_ = RegularTequilaOrderRecord.objects.get(
                id=request.data.get("customer_order_id")
            )
        except RegularTequilaOrderRecord.DoesNotExist:
            return Response(
                {"error": "Order selected does not exist"}, status.HTTP_200_OK
            )

        orders_to_remove = request.data.get("orders_to_remove")
        try:
            for order in orders_to_remove["regular_orders_to_remove"]:
                regular_order = object_.regular_items.get(id=order["item_id"])
                quantity_to_remove = order["quantity"]
                res_q = regular_order.quantity - quantity_to_remove
                if res_q < 0:
                    return Response(
                        {
                            "error": "There is only %d %s"
                                     % (regular_order.quantity, regular_order.item.item.name)
                        },
                        status.HTTP_400_BAD_REQUEST,
                    )
                elif res_q == 0:
                    object_.regular_items.remove(regular_order)
                    self.change_amount_paid(object_, regular_order, quantity_to_remove)
                    return Response(
                        {"success": "Item removed."},
                        status.HTTP_200_OK,
                    )
                else:
                    regular_order.quantity = res_q
                    regular_order.save()
                    try:
                        self.change_amount_paid(object_, regular_order, res_q)
                    except:
                        pass
                    return Response(
                        {"success": "Item removed."},
                        status.HTTP_200_OK,
                    )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def change_amount_paid(self, object_, regular_order, roq):  # regular_order_quantity
        payment_made = CustomerRegularTequilaOrderRecordPayment.objects.get(
            customer_regular_tequila_order_record__regular_tequila_order_record=object_,
            payment_started=True,
        )
        payment_made.amount_paid -= regular_order.get_price_of_items(roq)
        payment_made.save()

        # return Response({"message": "Order removed"}, status.HTTP_200_OK)

    def add_regular_orders(self, request, orders, object_):
        regular_orders: List[Dict] = orders["regular_orders"]
        self.create_regular_orders(request, object_, regular_orders)

    def add_tequila_orders(self, request, orders, object_):
        tequila_orders: List[Dict] = orders["tequila_orders"]
        self.create_tequila_orders(request, object_, tequila_orders)


class CustomerRegularTequilaOrderRecordViewSet(viewsets.ModelViewSet):
    """ Customer Regular And Tequila Order Record APIs """

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

        class Meta:
            model = CustomerRegularTequilaOrderRecord
            fields: List[str] = [
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
        return CustomerRegularTequilaOrderRecord.objects.select_related(
            "created_by",
            "regular_tequila_order_record",
            "regular_tequila_order_record__created_by",
        ).prefetch_related(
            "regular_tequila_order_record__regular_items",
            "regular_tequila_order_record__tequila_items",
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
                    "orders": q.get_orders_detail,
                })
        return Response(data=res, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs) -> Response:
        try:
            data = self.perform_create(request)

            return Response(data, status.HTTP_201_CREATED)

        except Exception as e:

            return Response({"message": str(e)}, status.HTTP_400_BAD_REQUEST)

    def perform_create(self, request) -> Dict:
        object_ = CustomerRegularTequilaOrderRecord.objects.create(
            customer_name=request.data.get("customer_name"),
            customer_phone=request.data.get("customer_phone"),
            regular_tequila_order_record=RegularTequilaOrderRecord.objects.get(
                id=request.data.get("order_id")
            ),
            customer_orders_number=str(
                orders_number_generator(
                    CustomerRegularTequilaOrderRecord, "customer_orders_number"
                )
            ),
            created_by=request.user,
            date_created=self.today
        )

        return {
            "customer_name": object_.customer_name,
            "customer_phone": object_.customer_phone,
            "customer_orders_number": object_.customer_orders_number,
            "orders": object_.get_orders_detail,
            "created_by": object_.created_by.username,
            "date_created": object_.date_created.timestamp()
        }

    @action(
        detail=False,
        methods=["GET"],
    )
    def search(self, request):
        try:
            customer_name = request.data["customer_name"]
            results = CustomerRegularTequilaOrderRecord.objects.filter(
                customer_name=customer_name
            )
            return Response(data=self.OutputSerializer(results, many=True).data, status=status.HTTP_200_OK)
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
        qs = self.get_queryset().filter(date_created__date=today_date)

        return Response(data=self.OutputSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["POST"],
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
            qs = self.get_queryset().filter(
                date_created__date__range=[from_date, to_date]
            )

            return Response(data=self.OutputSerializer(qs, many=True), status=status.HTTP_200_OK)
        except KeyError:
            return Response(
                {"message": "Invalid dates."}, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomerRegularTequilaOrderRecordPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerRegularTequilaOrderRecordPaymentSerializer
    today = timezone.localtime()

    def get_queryset(self):
        return CustomerRegularTequilaOrderRecordPayment.objects.select_related(
            "customer_regular_tequila_order_record", "created_by"
        )

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        response: Dict = {
            "id": instance.id,
            "customer_name": instance.customer_regular_tequila_order_record.customer_name,
            "customer_phone": instance.customer_regular_tequila_order_record.customer_phone,
            "customer_orders_number": instance.customer_regular_tequila_order_record.customer_orders_number,
            "payment_status": instance.payment_status,
            "payment_method": instance.payment_method,
            "amount_paid": float(instance.amount_paid),
            "amount_remaining": float(instance.get_remaining_amount),
            "orders": instance.customer_regular_tequila_order_record.get_orders_detail,
            "created_by": instance.created_by.username,
            "date_paid": str(instance.date_paid).split(" ")[0],
            "time_paid": str(instance.date_paid).split(" ")[1].split(".")[0],
        }
        return Response(response, status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        response: List[Dict] = self.get_list(self.get_queryset())

        return Response(response, status.HTTP_200_OK)

    def get_list(self, objects):
        response: List[Dict] = []
        [
            response.append(
                {
                    "id": payment.id,
                    "by_credit": payment.by_credit,
                    "customer_name": payment.customer_regular_tequila_order_record.customer_name,
                    "customer_phone": payment.customer_regular_tequila_order_record.customer_phone,
                    "customer_orders_number": payment.customer_regular_tequila_order_record.customer_orders_number,
                    "payment_status": payment.payment_status,
                    "payment_method": payment.payment_method,
                    "payable_amount": float(payment.get_total_amount_to_pay),
                    "paid_amount": float(payment.amount_paid),
                    "remained_amount": float(payment.get_remaining_amount),
                    "orders": payment.customer_regular_tequila_order_record.get_orders_detail,
                    "created_by": payment.created_by.username,
                    "date_paid": str(payment.date_paid).split(" ")[0],
                    "time_paid": str(payment.date_paid).split(" ")[1].split(".")[0],
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
        by_credit = request.data.get("by_credit")
        amount_paid = float(request.data.get("amount_paid"))
        customer = self.get_customer(request)
        customer_regular_order_record = CustomerRegularTequilaOrderRecord.objects.get(
            id=request.data.get("customer_order_record")
        )

        if customer_regular_order_record.get_remained_amount() <= 0:
            raise ValidationError("Order is already paid.")

        try:
            object_ = self.get_crtorp(customer_regular_order_record)
            self.alter_crtorp_amount_paid(amount_paid, object_)
            self.alter_crtrop_payment_status(object_)
            self.alter_ccrtrop_amount_paid(amount_paid, customer, object_)

            return {"message": "Success"}

        except CustomerRegularTequilaOrderRecordPayment.DoesNotExist:
            pass

        if (
                by_credit
                and self.get_advance_amount(customer_regular_order_record, amount_paid)
                > customer.credit_limit
        ):
            raise ValidationError(
                "Can't perform this operation. Customer's credit is not enough."
            )

        elif by_credit and self.get_advance_amount(
                customer_regular_order_record, amount_paid
        ) > self.get_remained_credit_for_today(customer):
            raise ValidationError(
                "Can't perform this operation. Remained credit for {} is {}".format(
                    customer.name, self.get_remained_credit_for_today(customer)
                )
            )

        object_ = CustomerRegularTequilaOrderRecordPayment.objects.create(
            customer_regular_tequila_order_record=customer_regular_order_record,
            amount_paid=amount_paid,
            created_by=request.user,
            payment_started=True,
            date_paid=self.today
        )

        self.pay_by_credit(request, by_credit, amount_paid, object_)
        self.save_payment_status(request, object_)

        object_.save()
        return {
            "customer_order_record": str(object_),
            "payment_status": object_.payment_status,
            "amount_paid": object_.amount_paid,
            "date_paid": object_.date_paid.timestamp(),
            "created_by": str(object_.created_by),
        }

    def alter_ccrtrop_amount_paid(self, amount_paid, customer, object_):
        ccrtorp = CreditCustomerRegularTequilaOrderRecordPayment.objects.filter(
            record_order_payment_record=object_,
            customer=customer,
            record_order_payment_record__by_credit=True,
        ).first()

        if ccrtorp:
            ccrtorp.amount_paid += amount_paid
            ccrtorp.save()

    def alter_crtrop_payment_status(self, object_):
        if object_.amount_paid >= object_.get_total_amount_to_pay:
            object_.payment_status = "paid"
        elif object_.amount_paid <= object_.get_total_amount_to_pay:
            object_.payment_status = "partial"
        else:
            object_.payment_status = "unpaid"
        object_.save()

    def alter_crtorp_amount_paid(self, amount_paid, object_):
        object_.amount_paid += amount_paid
        object_.save()

    def get_crtorp(self, customer_regular_order_record):
        return CustomerRegularTequilaOrderRecordPayment.objects.get(
            payment_started=True,
            customer_regular_tequila_order_record=customer_regular_order_record,
        )

    def pay_by_credit(self, request, by_credit, amount_paid, object_):
        customer = self.get_customer(request)
        if by_credit and customer:
            object_.by_credit = True
            object_.save()
            CreditCustomerRegularTequilaOrderRecordPayment.objects.create(
                record_order_payment_record=object_,
                customer=customer,
                amount_paid=amount_paid,
                date_created=self.today,
            )
            self._change_customer_details(object_, customer)
            send_notification(
                f"Chakula cha gharama ya shilingi {object_.customer_regular_tequila_order_record.regular_tequila_order_record.get_total_price()}/= kimenunuliwa kwa jina lako. Umelipia shilingi {str(amount_paid)}/=. Asante na Karibu tena.",
                customer.phone)

    def _change_customer_details(self, object_, customer):
        customer_regular_order_record = object_.customer_regular_tequila_order_record
        customer_regular_order_record.customer_name = customer.name
        customer_regular_order_record.customer_phone = customer.phone
        customer_regular_order_record.save()

    def save_payment_status(self, request, object):
        amount_paid = float(request.data.get("amount_paid"))
        if amount_paid == 0:
            object.payment_status = "unpaid"
        elif amount_paid >= object.get_total_amount_to_pay:
            object.payment_status = "paid"
        else:
            object.payment_status = "partial"

    def get_customer(self, request):
        try:
            customer = CreditCustomer.objects.get(id=request.data.get("customer_id"))
        except CreditCustomer.DoesNotExist:
            customer = None
        return customer

    def get_remained_credit_for_today(self, customer) -> float:

        return customer.credit_limit - self.get_today_spend(
            customer
        )  # 20,000 - 15,000 = 5,000

    def get_today_spend(self, customer) -> float:
        total_amount: float = 0.0
        qs = self.get_credit_qs(customer)
        for q in qs:
            total_amount += q.get_credit_payable_amount()

        return total_amount  # 15,000.0

    def get_credit_qs(self, customer):
        return CreditCustomerRegularTequilaOrderRecordPayment.objects.filter(
            customer=customer, date_created=self.today
        )

    def get_advance_amount(self, customer_regular_order_record, amount_paid) -> float:
        """This is the amount of money customer wants to pay in advance"""

        return (
                customer_regular_order_record.regular_tequila_order_record.get_total_price()
                - amount_paid
        )

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_all_paid(self, request, *args, **kwargs):
        res: List[Dict] = []
        filtered_qs = self.get_queryset().filter(payment_status="paid")
        [
            res.append(
                {
                    "customer_name": qs.customer_regular_tequila_order_record.customer_name,
                    "customer_phone": qs.customer_regular_tequila_order_record.customer_phone,
                    "customer_orders_number": qs.customer_regular_tequila_order_record.customer_orders_number,
                    "paid_amount": float(qs.amount_paid),
                    "date_paid": str(qs.date_paid).split(" ")[0],
                    "time_paid": str(qs.date_paid).split(" ")[1].split(".")[0],
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
        res: List[Dict] = []
        filtered_qs = self.get_queryset().filter(payment_status="partial")
        [
            res.append(
                {
                    "customer_name": qs.customer_regular_tequila_order_record.customer_name,
                    "customer_phone": qs.customer_regular_tequila_order_record.customer_phone,
                    "customer_orders_number": qs.customer_regular_tequila_order_record.customer_orders_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                    "paid_amount": qs.amount_paid,
                    "remaining_amount": qs.get_remaining_amount,
                    "date_paid": str(qs.date_paid).split(" ")[0],
                    "time_paid": str(qs.date_paid).split(" ")[1].split(".")[0],
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
        filtered_qs = self.get_queryset().filter(payment_status="unpaid")
        [
            res.append(
                {
                    "customer_name": qs.customer_regular_tequila_order_record.customer_name,
                    "customer_phone": qs.customer_regular_tequila_order_record.customer_phone,
                    "customer_orders_number": qs.customer_regular_tequila_order_record.customer_orders_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                }
            )
            for qs in filtered_qs
        ]
        return Response(res, status.HTTP_200_OK)


class CreditCustomerRegularTequilaOrderRecordPaymentHistoryViewSet(
    viewsets.ModelViewSet
):
    serializer_class = CreditCustomerRegularTequilaOrderRecordPaymentHistorySerializer

    def get_queryset(self):
        return CreditCustomerRegularTequilaOrderRecordPaymentHistory.objects.select_related(
            "credit_customer_payment__record_order_payment_record__customer_regular_tequila_order_record"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"message": f"{serializer.errors}"}, status.HTTP_400_BAD_REQUEST
            )
        credit_customer_payment = request.data.get("credit_customer_payment")
        try:
            object = CreditCustomerRegularTequilaOrderRecordPayment.objects.get(
                id=credit_customer_payment
            )
            if (
                    object.record_order_payment_record.payment_status == "paid"
                    or object.record_order_payment_record.by_credit is False
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
        except CreditCustomerRegularTequilaOrderRecordPayment.DoesNotExist:
            return Response(
                {"message": "Customer Order Chosen does not exists."},
                status.HTTP_400_BAD_REQUEST,
            )


# Sales Changes Ends


class CreditCustomerRegularOrderRecordPaymentHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = CreditCustomerRegularOrderRecordPaymentHistorySerializer

    def get_queryset(self):
        return CreditCustomerRegularOrderRecordPaymentHistory.objects.select_related(
            "credit_customer_payment__record_order_payment_record__customer_order_record"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"message": f"{serializer.errors}"}, status.HTTP_400_BAD_REQUEST
            )
        credit_customer_payment = request.data.get("credit_customer_payment")
        try:
            object = CreditCustomerRegularOrderRecordPayment.objects.get(
                id=credit_customer_payment
            )
            if (
                    object.record_order_payment_record.payment_status == "paid"
                    or object.record_order_payment_record.by_credit is False
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
        except CreditCustomerRegularOrderRecordPayment.DoesNotExist:
            return Response(
                {"message": "Credit Dish Chosen does not exists."},
                status.HTTP_400_BAD_REQUEST,
            )


class BarPayrolViewSet(viewsets.ModelViewSet):
    serializer_class = BarPayrolSerializer

    def get_queryset(self):
        return BarPayrol.objects.select_related("bar_payer")

    def update(self, request, pk=None):
        instance = self.get_object()
        bar_payee = request.data.get("bar_payee")
        amount_paid = request.data.get("amount_paid")
        payment_method = request.data.get("payment_method")
        if bar_payee:
            instance.name = request.data.get("name")
        if amount_paid:
            instance.amount_paid = amount_paid
        if payment_method:
            instance.payment_method = payment_method
        instance.save()

        return Response({"message": "Operation success"}, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            object_ = serializer.save(bar_payer=request.user)
            data = {
                "payee": object_.name,
                "payer": object_.bar_payer.username,
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
        response: List = []
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
        response: Dict = {}
        response["total_amount_paid"] = (
                payments_this_month.aggregate(total=Sum("amount_paid"))["total"] or 0
        )
        payments: List[Dict] = []
        [
            payments.append(
                {
                    "id": payment.id,
                    "payee": payment.name,
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


# Sale Tequilas


class BarTequilaItemViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return TequilaInventoryRecordsTrunk.objects.select_related("item", "item__unit").prefetch_related(
            "tequila_inventory_record")

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        self.append_regular(response)
        return Response(data=response, status=status.HTTP_200_OK)

    def append_regular(self, response: List[Dict]):
        for item in self.get_queryset():
            if item.get_items_to_sale():
                response.append(item.get_items_to_sale())
        return response


class TequilaOrderRecordViewSet(viewsets.ModelViewSet):
    serializer_class = TequilaOrderRecordSerializer

    def get_queryset(self):
        return TequilaOrderRecord.objects.select_related(
            "item", "item__item", "created_by"
        )

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
                "date_created": str(instance.date_created).split(" ")[0],
                "time_created": str(instance.date_created).split(" ")[1].split(".")[0],
            },
            status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        response: List[Dict] = []
        [
            response.append(
                {
                    "id": record.id,
                    "item": record.item.item.name,
                    "ordered_quantity": record.quantity,
                    "total_price": record.total,
                    "order_number": record.order_number,
                    "created_by": record.created_by.username,
                    "date_created": str(record.date_created).split(" ")[0],
                    "time_created": str(record.date_created)
                        .split(" ")[1]
                        .split(".")[0],
                }
            )
            for record in self.get_queryset()
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
            order_number=str(
                orders_number_generator(TequilaOrderRecord, "order_number")
            ),
            created_by=request.user,
            date_created=timezone.now(),
        )
        return {
            "id": object.id,
            "item": object.item.item.name,
            "quantity": object.quantity,
            "order_number": object.order_number,
            "created_by": object.created_by.username,
            "date_created": str(object.date_created).split(" ")[0],
            "time_created": str(object.date_created).split(" ")[1].split(".")[0],
        }


class CustomerTequilaOrderRecordViewSet(viewsets.ModelViewSet):
    serializer_class = TequilaCustomerOrderRecordSerializer

    def get_queryset(self):
        return CustomerTequilaOrderRecord.objects.select_related(
            "created_by"
        ).prefetch_related("orders")

    def retrieve(self, request, pk=None) -> Dict:
        instance = self.get_object()
        response: Dict = {
            "id": instance.id,
            "customer_name": instance.customer_name,
            "customer_phone": instance.customer_phone,
            "dish_number": instance.customer_orders_number,
            "payment_status": instance.get_payment_status(),
            "payable_amount": float(instance.get_total_price),
            "paid_amount": float(instance.get_paid_amount()),
            "remained_amount": float(instance.get_remained_amount()),
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
            customer_orders_number=str(
                orders_number_generator(
                    CustomerTequilaOrderRecord, "customer_orders_number"
                )
            ),
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
                order_number=str(
                    orders_number_generator(TequilaOrderRecord, "order_number")
                ),
                created_by=request.user,
            )
            object.orders.add(order)
        object.save()

    def list(self, request, *args, **kwargs):

        return Response(self.get_list(self.get_queryset()), status.HTTP_200_OK)

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
        qs = self.get_queryset().filter(date_created__date=todays_date)
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
            qs = self.get_queryset().filter(
                date_created__date__range=[from_date, to_date]
            )
            response = self.append_orders(qs)
            return Response(response, status.HTTP_200_OK)
        except KeyError:
            return Response(
                {"message": "Invalid dates."}, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def append_orders(self, qs):

        return self.appending(qs)

    def appending(self, objects) -> List[Dict]:
        res: List[Dict] = []
        [
            res.append(
                {
                    "id": _.id,
                    "customer_name": _.customer_name,
                    "customer_phone": _.customer_phone,
                    "dish_number": _.customer_orders_number,
                    "payment_status": _.get_payment_status(),
                    "payable_amount": float(_.get_total_price),
                    "paid_amount": float(_.get_paid_amount()),
                    "remained_amount": float(_.get_remained_amount()),
                    "orders": _.get_orders_detail,
                }
            )
            for _ in objects
        ]

        return res


class CustomerTequilaOrderRecordPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = TequilaCustomerOrderRecordPaymentSerializer
    today = timezone.localdate()

    def get_queryset(self):
        return CustomerTequilaOrderRecordPayment.objects.select_related(
            "customer_order_record", "created_by"
        )

    def retrieve(self, request, pk=None) -> Response:
        instance = self.get_object()
        response: Dict = {
            "id": instance.id,
            "by_credit": instance.by_credit,
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

    def list(self, request, *args, **kwargs) -> Response:
        response: List[dict] = self.get_list(self.get_queryset())

        return Response(response, status.HTTP_200_OK)

    def get_list(self, objects) -> List[Dict]:
        response: List[Dict] = []
        [
            response.append(
                {
                    "id": payment.id,
                    "by_credit": payment.by_credit,
                    "customer_name": payment.customer_order_record.customer_name,
                    "customer_phone": payment.customer_order_record.customer_phone,
                    "customer_orders_number": payment.customer_order_record.customer_orders_number,
                    "payment_status": payment.payment_status,
                    "payment_method": payment.payment_method,
                    "payable_amount": float(payment.get_total_amount_to_pay),
                    "paid_amount": float(payment.amount_paid),
                    "remained_amount": float(payment.get_remaining_amount),
                    "orders": payment.customer_order_record.get_orders_detail,
                    "created_by": payment.created_by.username,
                    "date_created": str(payment.date_paid).split(" ")[0],
                    "time_created": str(payment.date_paid).split(" ")[1].split(".")[0],
                }
            )
            for payment in objects
        ]

        return response

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self.perform_create(request)

        return Response(data, status.HTTP_201_CREATED)

    def perform_create(self, request):
        by_credit = request.data.get("by_credit")
        amount_paid = request.data.get("amount_paid")
        customer = self.get_customer(request)
        customer_order_record = CustomerTequilaOrderRecord.objects.get(
            id=request.data.get("customer_order_record")
        )

        if customer_order_record.get_remained_amount() <= 0:
            raise ValidationError("Order is already paid.")

        try:
            object = CustomerTequilaOrderRecordPayment.objects.get(
                payment_started=True,
                customer_order_record=customer_order_record,
            )
            object.amount_paid = object.amount_paid + amount_paid
            object.save()
            if object.amount_paid >= object.get_total_amount_to_pay:
                object.payment_status = "paid"
            elif object.amount_paid <= object.get_total_amount_to_pay:
                object.payment_status = "partial"
            else:
                object.payment_status = "unpaid"
            object.save()

            return Response(status.HTTP_200_OK)
        except CustomerTequilaOrderRecordPayment.DoesNotExist:
            pass

        if (
                by_credit
                and self.get_advance_amount(customer_order_record, amount_paid)
                > customer.credit_limit
        ):
            raise ValidationError(
                "Can't perform this operation. Customer's credit is not enough."
            )

        elif by_credit and self.get_advance_amount(
                customer_order_record, amount_paid
        ) > self.get_remained_credit_for_today(customer):
            raise ValidationError(
                "Can't perform this operation. Remained credit for {} is {}".format(
                    customer.name, self.get_remained_credit_for_today(customer)
                )
            )
        object = CustomerTequilaOrderRecordPayment.objects.create(
            customer_order_record=customer_order_record,
            amount_paid=amount_paid,
            payment_started=True,
            created_by=request.user,
        )
        self.pay_by_credit(request, by_credit, object)
        self.save_payment_status(request, object)
        object.change_payment_status()
        object.save()
        return {
            "customer_order_record": str(object),
            "payment_status": object.payment_status,
            "amount_paid": object.amount_paid,
            "date_paid": str(object.date_paid).split(" ")[0],
            "time_paid": str(object.date_paid).split(" ")[1].split(".")[0],
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
                date_created=timezone.localdate(),
            )
            self._change_customer_details(object, customer)

    def _change_customer_details(self, object, customer):
        customer_order_record = object.customer_order_record
        customer_order_record.customer_name = customer.name
        customer_order_record.customer_phone = customer.phone
        customer_order_record.save()

    def get_remained_credit_for_today(self, customer) -> float:

        return customer.credit_limit - self.get_today_spend(
            customer
        )  # 20,000 - 15,000 = 5,000

    def get_today_spend(self, customer) -> float:
        total_amount: float = 0.0
        qs = self.get_credit_qs(customer)
        for q in qs:
            total_amount += q.get_credit_payable_amount()

        return total_amount  # 15,000

    def get_credit_qs(self, customer):
        return CreditCustomerTequilaOrderRecordPayment.objects.filter(
            customer=customer, date_created=self.today
        )

    def get_advance_amount(self, customer_order_record, amount_paid) -> float:
        """This is the amount of money customer wants to pay in advance"""

        return customer_order_record.get_total_price - amount_paid

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
            customer = CreditCustomer.objects.get(id=request.data.get("customer_id"))
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
        res: List[Dict] = []
        filtered_qs = self.get_queryset().filter(payment_status="paid")
        [
            res.append(
                {
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "paid_amount": float(qs.amount_paid),
                    "date_paid": str(qs.date_paid).split(" ")[0],
                    "time_paid": str(qs.date_paid).split(" ")[1].split(".")[0],
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
        res: List[Dict] = []
        filtered_qs = self.get_queryset().filter(payment_status="partial")
        [
            res.append(
                {
                    "customer_name": qs.customer_order_record.customer_name,
                    "customer_phone": qs.customer_order_record.customer_phone,
                    "customer_orders_number": qs.customer_order_record.customer_orders_number,
                    "payable_amount": qs.get_total_amount_to_pay,
                    "paid_amount": qs.amount_paid,
                    "remaining_amount": qs.get_remaining_amount,
                    "date_paid": str(qs.date_paid).split(" ")[0],
                    "time_paid": str(qs.date_paid).split(" ")[1].split(".")[0],
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
        filtered_qs = self.get_queryset().filter(payment_status="unpaid")
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


class CreditCustomerTequilaOrderRecordPaymentHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = CreditCustomerTequilaOrderRecordPaymentHistorySerializer

    def get_queryset(self):
        return CreditCustomerTequilaOrderRecordPaymentHistory.objects.select_related(
            "credit_customer_payment__record_order_payment_record__customer_order_record"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"message": f"{serializer.errors}"}, status.HTTP_400_BAD_REQUEST
            )
        credit_customer_payment = request.data.get("credit_customer_payment")
        try:
            object = CreditCustomerTequilaOrderRecordPayment.objects.get(
                id=credit_customer_payment
            )
            if (
                    object.record_order_payment_record.payment_status == "paid"
                    or object.record_order_payment_record.by_credit is False
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
        except CreditCustomerTequilaOrderRecordPayment.DoesNotExist:
            return Response(
                {"message": "Credit Dish Chosen does not exists."},
                status.HTTP_400_BAD_REQUEST,
            )
