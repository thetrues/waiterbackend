from typing import Dict
from user.serializers import RegistrationSerializer, UserSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import login, authenticate
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status
from user.models import User
from icecream import ic


class RegistrationView(APIView):
    """Registration View"""

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = self.create_acount(serializer)
        else:
            data = serializer.errors
        return Response(data, status=status.HTTP_200_OK)

    def create_acount(self, serializer):
        user = serializer.save()

        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "mobile_phone": user.mobile_phone,
            "username": user.username,
            "user_type": user.user_type,
        }


class LoginView(APIView):
    """Login View"""

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            data: dict = {"message": "Login success"}
        else:
            data: dict = {"message": "Invalid credentials"}
        return Response(data, status.HTTP_200_OK)


class GetAllUsersView(APIView):
    """GetUsersView

    get(self, request, format="JSON")
        Returns a list of users
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        """Returns a list of all users"""

        request_user_id: int = request.user.id
        users = User.objects.exclude(id=request_user_id)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ManageUserView(APIView):
    """User Management APIs

    get_object(self, pk) -> user or None:
        returns user object is any or None if not found.

    get(self, request, pk, format=None) -> user:
        returns user object found from get_object(self, pk).

    put(self, request, pk, format=None) -> user:
        update user details and returns user object.

    delete(self, request, pk, format=None) -> None:
        delete user and returns None.
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self, pk):
        """Get user instance"""
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def get(self, request, pk, format=None):
        """Get user instance"""
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        """Update user instance"""
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete user instance"""
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_200_OK)


class ChangeUserPasswordView(APIView):
    """Change User Password API

    get_object(self, pk) -> user:
        get user instance

    post(self, request, pk, format=None) -> dict:
        set or change user password and returns user object
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self, pk):
        """Get user instance"""
        try:
            return User.objects.get(pk=pk)
        except:
            raise NotFound

    def put(self, request, pk, *args, **kwargs):
        data: Dict = {}
        """update user password and returns user object."""
        user = self.get_object(pk=pk)
        user.set_password(request.data["password"])
        user.save()
        data = {"message": "Password changed."}
        return Response(data=data, status=status.HTTP_200_OK)


class ActivateDeactivateUserAccountView(APIView):
    """Activate or Deactivate a user account API

    post(self, request, pk, format=None) -> user:
        Activate or Deactivate a user account.
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self, pk):
        """Get user instance"""
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            ic("User does not exist")
            raise NotFound

    def post(self, request, pk, *args, **kwargs):
        """Deactivate or Activate user account"""
        user = self.get_object(pk)
        user.is_active = not user.is_active
        user.save()
        data: dict = {"message": "Operation Success."}
        return Response(data=data, status=status.HTTP_200_OK)


class CustomAuthTokenView(ObtainAuthToken):
    """Get or Create a user authentication token API

    post(self, request, *args, **kwargs) -> dict:
        get or create a new auth token for a user.
    """

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
