from django.contrib.auth.models import User
from rest_framework import serializers

class RegistrationSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    repeated_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        pw = attrs.get('password')
        repw = attrs.get('repeated_password')
        if pw != repw:
            raise serializers.ValidationError({'repeated_password': 'Passwords do not match.'})

        email = attrs.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'This email address is already in use.'})
        return attrs

    def create(self, validated_data):
        fullname = validated_data['fullname']
        email = validated_data['email']
        password = validated_data['password']

        # wir verwenden die E-Mail als username (Standard-Usermodell)
        username = email

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fullname  # „fullname“ legen wir pragmatisch in first_name ab
        )
        return user
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = (attrs.get('email') or '').strip()
        password = attrs.get('password') or ''

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # absichtlich generische Meldung
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        if not user.check_password(password):
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        attrs['user'] = user
        return attrs
