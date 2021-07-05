from core.serializers import (
    AdditiveSerializer,
    InventoryRecordSerializer,
    ItemSerializer,
    MenuSerializer,
)
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from core.models import Additive, InventoryRecord, Item, Menu
from rest_framework.views import APIView
from user.models import User
from icecream import ic


class ItemView(APIView):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Returns a list of all items"""
        items = Item.objects.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """Create item instance"""
        data: dict = {}
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = {"message": "Item created."}
        else:
            data = serializer.errors
        return Response(data=data, status=status.HTTP_200_OK)


class ManageItemView(APIView):
    """Item Management APIs

    get_object(self, pk) -> item or None:
            returns item object is any or None if not found.

    get(self, request, pk, format=None) -> item:
            returns item object found from get_object(self, pk).

    put(self, request, pk, format=None) -> item:
            update item details and returns item object.

    delete(self, request, pk, format=None) -> None:
            delete item and returns None.
    """

    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get_object(self, pk):
        """Get item instance"""
        try:
            return Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise NotFound

    def get(self, request, pk, format=None):
        """Get item instance"""
        item = self.get_object(pk)
        serializer = ItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        """Update item instance"""
        item = self.get_object(pk)
        serializer = ItemSerializer(instance=item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete item instance"""
        item = self.get_object(pk)
        item.delete()
        return Response(status=status.HTTP_200_OK)


class MenuView(APIView):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Returns a list of all menu"""
        menu = Menu.objects.all()
        serializer = MenuSerializer(menu, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """Create menu instance"""
        data: dict = {}
        serializer = MenuSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = {"message": "Menu created."}
        else:
            data = serializer.errors
        return Response(data=data, status=status.HTTP_200_OK)


class ManageMenuView(APIView):
    """Menu Management APIs

    get_object(self, pk) -> menu or None:
            returns menu object is any or None if not found.

    get(self, request, pk, format=None) -> menu:
            returns menu object found from get_object(self, pk).

    put(self, request, pk, format=None) -> menu:
            update menu details and returns menu object.

    delete(self, request, pk, format=None) -> None:
            delete menu and returns None.
    """

    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get_object(self, pk):
        """Get menu instance"""
        try:
            return Menu.objects.get(pk=pk)
        except Menu.DoesNotExist:
            raise NotFound

    def get(self, request, pk, format=None):
        """Get menu instance"""
        menu = self.get_object(pk)
        serializer = MenuSerializer(menu)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        """Update menu instance"""
        menu = self.get_object(pk)
        serializer = MenuSerializer(instance=menu, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete menu instance"""
        menu = self.get_object(pk)
        menu.delete()
        return Response(status=status.HTTP_200_OK)


class AdditiveView(APIView):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Returns a list of all additives"""
        additives = Additive.objects.all()
        serializer = AdditiveSerializer(additives, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """Create additive instance"""
        data: dict = {}
        serializer = AdditiveSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = {"message": "Additive created."}
        else:
            data = serializer.errors
        return Response(data=data, status=status.HTTP_200_OK)


class ManageAdditiveView(APIView):
    """Additive Management APIs

    get_object(self, pk) -> additive or None:
            returns additive object is any or None if not found.

    get(self, request, pk, format=None) -> additive:
            returns additive object found from get_object(self, pk).

    put(self, request, pk, format=None) -> additive:
            update additive details and returns additive object.

    delete(self, request, pk, format=None) -> None:
            delete additive and returns None.
    """

    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get_object(self, pk):
        """Get additive instance"""
        try:
            return Additive.objects.get(pk=pk)
        except Additive.DoesNotExist:
            raise NotFound

    def get(self, request, pk, format=None):
        """Get additive instance"""
        additive = self.get_object(pk)
        serializer = AdditiveSerializer(additive)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        """Update additive instance"""
        additive = self.get_object(pk)
        serializer = AdditiveSerializer(instance=additive, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete additive instance"""
        additive = self.get_object(pk)
        additive.delete()
        return Response(status=status.HTTP_200_OK)


class InventoryRecordView(APIView):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Returns a list of all inventory records"""
        data: list = []
        temp_dict: dict = {}
        queryset = InventoryRecord.objects.all()
        data = self.get_inventory_records(data, temp_dict, queryset)
        return Response(data, status=status.HTTP_200_OK)

    def get_inventory_records(self, data, temp_dict, queryset) -> list():
        for record in queryset:
            temp_dict["record_id"] = record.id
            temp_dict["item"] = {
                "item_id": record.item.id,
                "name": record.item.name,
                "unit": record.item.unit,
            }
            temp_dict["quantity"] = record.quantity
            temp_dict["price"] = record.price
            temp_dict["threshold"] = record.threshold
            temp_dict["created_at"] = record.created_at
            temp_dict["updated_at"] = record.updated_at
            temp_dict["created_by"] = record.created_by.username
            data.append(temp_dict)
            temp_dict = {}
        return data

    def post(self, request, format=None):
        """Create inventory record instance"""
        try:
            InventoryRecord.objects.create(
                item=Item.objects.get(name=request.data.get("item")),
                price=request.data.get("price"),
                quantity=request.data.get("quantity"),
                threshold=request.data.get("threshold"),
                created_by=User.objects.get(username=request.data.get("created_by")),
            )
            data = {"success": "Operation success"}
        except Exception as e:
            ic(e)
            data = {"message": "Error occurred"}
        return Response(data=data, status=status.HTTP_200_OK)
