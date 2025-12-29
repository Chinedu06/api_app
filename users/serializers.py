from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SupplierProfile
from django.conf import settings

User = get_user_model()


class OperatorRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            role=User.ROLE_OPERATOR,
            is_verified=False
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class OperatorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        user = authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_verified:
            raise serializers.ValidationError("Account not yet approved by admin.")

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'username': user.username,
                'email': user.email,
                'role': user.role,
            }
        }


class SupplierProfileSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    association_certificate_url = serializers.SerializerMethodField()
    business_certificate_url = serializers.SerializerMethodField()

    class Meta:
        model = SupplierProfile
        fields = [
            'id', 'user', 'trading_name', 'company_name', 'registration_number',
            'business_address', 'business_phone', 'business_email',
            'owner_full_name', 'owner_phone', 'owner_email',
            'contact_person_name', 'contact_person_phone', 'contact_person_email',
            'association_certificate', 'business_certificate',
            'association_certificate_url', 'business_certificate_url',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            'association_certificate_url', 'business_certificate_url'
        ]

    def get_association_certificate_url(self, obj):
        if obj.association_certificate:
            return f"{settings.MEDIA_URL}{obj.association_certificate}"
        return None

    def get_business_certificate_url(self, obj):
        if obj.business_certificate:
            return f"{settings.MEDIA_URL}{obj.business_certificate}"
        return None

    def validate(self, data):
        return data
