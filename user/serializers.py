from rest_framework import serializers
from user.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=128, min_length=6)
    first_name = serializers.CharField(max_length=255, min_length=1, required=True)
    last_name = serializers.CharField(max_length=255, min_length=1, required=True)
    mobile_phone = serializers.CharField(max_length=15, min_length=10, required=True)
    password = serializers.CharField(write_only=True, max_length=128, min_length=6)
    confirm_password = serializers.CharField(
        write_only=True, max_length=128, min_length=6
    )

    def save(self):
        user_type = self.validated_data.get("user_type")
        user = User(
            first_name=self.validated_data.get("first_name"),
            last_name=self.validated_data.get("last_name"),
            mobile_phone=self.validated_data.get("mobile_phone"),
            username=self.validated_data.get("username"),
            user_type=self.validated_data.get("user_type"),
        )
        if user_type == "manager":
            user.is_staff = True

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
            "user_type",
            "username",
            "password",
            "confirm_password",
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "user_type",
            "mobile_phone",
            "is_active",
            "is_staff",
        ]
    
    def to_representation(self, instance):
        rep = super(UserSerializer, self).to_representation(instance)
        rep["user_type"] = instance.get_user_type_display()
        return rep
