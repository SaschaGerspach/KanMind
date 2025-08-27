from django.contrib.auth.models import User
from rest_framework import serializers


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Validates matching passwords and unique email, then creates the user.
    """

    fullname = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    repeated_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        """
        Ensure passwords match and the email is not already in use.
        """
        pw = attrs.get('password')
        repw = attrs.get('repeated_password')
        if pw != repw:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )

        email = attrs.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {'email': 'This email address is already in use.'}
            )
        return attrs

    def create(self, validated_data):
        """
        Create a user account. Uses email as username and stores the
        provided 'fullname' in first_name for simplicity.
        """
        fullname = validated_data['fullname']
        email = validated_data['email']
        password = validated_data['password']

        # Use the email as the username (default User model)
        username = email

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fullname,  # store 'fullname' pragmatically in first_name
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login validation.
    Resolves the user by case-insensitive email and checks the password.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Validate credentials and attach the authenticated user to attrs.
        """
        email = (attrs.get('email') or '').strip()
        password = attrs.get('password') or ''

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        if not user.check_password(password):
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        attrs['user'] = user
        return attrs
