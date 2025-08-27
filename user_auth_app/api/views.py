from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.authtoken.models import Token
from .serializers import RegistrationSerializer, LoginSerializer
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


class RegistrationView(APIView):
    """
    Register a new user account and return an auth token.
    Public endpoint (no authentication required).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validate incoming payload with RegistrationSerializer,
        create the user, and issue a token.
        """
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        data = {
            "token": token.key,
            "fullname": user.first_name,  # value originally captured from "fullname" field in request
            "email": user.email,
            "user_id": user.id,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Email/password login with basic inline validation.
    Applies scoped rate limiting under scope 'login'.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        """
        Resolve user by email (case-insensitive), verify password,
        and return (create if needed) an auth token.
        """
        email = request.data.get('email', '')
        password = request.data.get('password', '')

        # Case-insensitive email match
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        data = {
            "token": token.key,
            "fullname": user.first_name,
            "email": user.email,
            "user_id": user.id,
        }
        return Response(data, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    Email/password login using LoginSerializer for validation.
    Public endpoint.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validate credentials via LoginSerializer, return/create token on success.
        """
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "fullname": user.first_name,   # stored during registration from "fullname" input
            "email": user.email,
            "user_id": user.id
        }, status=status.HTTP_200_OK)


class EmailCheckView(APIView):
    """
    Authenticated endpoint to verify whether an email exists.
    Returns a minimal user representation when found.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Validate the 'email' query parameter (presence + format),
        perform a case-insensitive lookup, and return id/email/fullname if found.
        """
        # 1) Read and normalize query parameter
        raw_email = request.query_params.get("email", "")
        email = raw_email.strip()

        # 2) Validate presence and format
        if not email:
            return Response(
                {"detail": "Query parameter 'email' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use DRF's EmailField for syntactic validation
        try:
            serializers.EmailField().run_validation(email)
        except serializers.ValidationError:
            return Response(
                {"detail": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) Case-insensitive lookup (narrow selection to required fields)
        user = User.objects.filter(email__iexact=email).only(
            "id", "email", "first_name", "last_name", "username"
        ).first()

        if not user:
            return Response(
                {"detail": "Email not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 4) Build display name (fallback to username)
        fullname = f"{user.first_name} {user.last_name}".strip() or user.username

        return Response(
            {"id": user.id, "email": user.email, "fullname": fullname},
            status=status.HTTP_200_OK,
        )
