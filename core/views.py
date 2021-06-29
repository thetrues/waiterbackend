from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from core.serializers import ItemSerializer
from rest_framework.views import APIView
from core.models import Item


class ItemView(APIView):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Returns a list of all items"""
        print(request)
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
        serializer = ItemSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete item instance"""
        item = self.get_object(pk)
        item.delete()
        return Response(status=status.HTTP_200_OK)
