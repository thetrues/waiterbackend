from user.serializers import RegistrationSerializer, UserSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status
from user.models import User


class RegistrationView(APIView):
    """Registration View"""

    def post(self, request):
        data: dict = {}
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data["response"] = "User account created."
            data["username"] = user.username
            token = Token.objects.get(user=user).key
            data["token"] = token
        else:
            data = serializer.errors
        return Response(data, status=status.HTTP_200_OK)


class GetAllUsersView(APIView):
    """GetUsersView

    get(self, request, format=None)
        Returns a list of users
    """

    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Returns a list of all users"""
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ManageUserView(APIView):
    """
    Retrieve, update or delete a user instance.
    """

    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get_object(self, pk):
        """Get user instance"""
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, pk, format=None):
        """Get user instance"""
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update user instance"""
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete user instance"""
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomAuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        """get or create a new auth token for a user."""
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user_id": user.pk, "username": user.username}
        )
