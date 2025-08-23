import email
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied


from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.validators import EmailValidator

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        max_length=150,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        error_messages={
            'required': 'Username is required.',
            'max_length': 'Username cannot be more than 150 characters.'
        }
    )
    
    email = serializers.EmailField(
        required=True,
        validators=[EmailValidator()],
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Enter a valid email address.'
        }
    )
    
    first_name = serializers.CharField(
        required=False,
        max_length=150,
        allow_blank=True,
        help_text="Optional. Enter your first name."
    )
    
    last_name = serializers.CharField(
        required=False,
        max_length=150,
        allow_blank=True,
        help_text="Optional. Enter your last name."
    )
    
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        required=True,
        help_text="Required. At least 6 characters.",
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required.',
            'min_length': 'Password must be at least 6 characters long.'
        }
    )

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "first_name", "last_name", 
                 "password"]
        
    def validate(self, attrs):
        # Get the user from the context
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to register new users.")

        # Check if user has permission to create users
        user = request.user
        if not (user.is_staff or user.is_agent or hasattr(user, 'farmer_profile')):
            raise PermissionDenied(
                "Only administrators, agents, and farmers can register new users."
            )

        return super().validate(attrs)

    def validate_email(self, value):
        User = get_user_model()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate_username(self, value):
        User = get_user_model()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = get_user_model().objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


