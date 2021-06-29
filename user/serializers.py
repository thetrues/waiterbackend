from rest_framework import serializers
from user.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    def save(self):
        user = User(
            first_name=self.validated_data["first_name"],
            last_name=self.validated_data["last_name"],
            mobile_phone=self.validated_data["mobile_phone"],
            username=self.validated_data["username"],
        )
        password = self.validated_data["password"]
        confirm_password = self.validated_data["confirm_password"]
        if password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords must match."})
        user.set_password(password)
        user.save()
        return user

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "mobile_phone",
            "username",
            "password",
            "confirm_password",
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "mobile_phone"]
