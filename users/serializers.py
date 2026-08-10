from rest_framework import serializers
from .models import CustomUser
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'slug', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],  # Use email as username
            email=validated_data['email'],
            password=validated_data['password']
        )
        Token.objects.create(user=user)  # Create a token for the new user
        return user

    def validate_password(self, value):
        validate_password(value)
        return value

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'slug']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Enter your email address")
    password = serializers.CharField(write_only=True, help_text="Enter your password")

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(
        required=True, 
        error_messages={"required":"Ad zorunlu.", "blank": "Ad boş olamaz"})
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id','email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, value):
        if password := value.get('password') != value.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],  # Use email as username
            email=validated_data['email'],
            password=validated_data['password']
        )
        Token.objects.create(user=user)  # Create a token for the new user
        return user

""" class UserAdminSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False)
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "slug", "role"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["role"] = "admin" if instance.is_superuser else "user"
        return rep

    def update(self, instance, validated_data):
        role = validated_data.pop("role", None)
        instance = super().update(instance, validated_data)

        if role:
            if role == "admin":
                instance.is_superuser = True
                instance.is_staff = True
            elif role == "user":
                instance.is_superuser = False
                instance.is_staff = False
            instance.save()

        return instance """

    