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
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        data = {
            "token": token.key,
            "fullname": user.first_name,  # kommt aus dem Requestfeld „fullname“
            "email": user.email,
            "user_id": user.id
        }
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        email = request.data.get('email', '')
        password = request.data.get('password', '')

        # E-Mail case-insensitiv suchen
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
            "user_id": user.id
        }
        return Response(data, status=status.HTTP_200_OK)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "fullname": user.first_name,   # in der Registration als fullname gespeichert
            "email": user.email,
            "user_id": user.id
        }, status=status.HTTP_200_OK)
    


class EmailCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1) E-Mail aus Query
        raw_email = request.query_params.get("email", "")
        email = raw_email.strip()

        # 2) Validierung: vorhanden + Format
        if not email:
            return Response(
                {"detail": "Query parameter 'email' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Nutzen DRF-Validator für E-Mail-Format
        try:
            serializers.EmailField().run_validation(email)
        except serializers.ValidationError:
            return Response(
                {"detail": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) Lookup (case-insensitive)
        user = User.objects.filter(email__iexact=email).only(
            "id", "email", "first_name", "last_name", "username"
        ).first()

        if not user:
            return Response(
                {"detail": "Email not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 4) fullname bauen
        fullname = f"{user.first_name} {user.last_name}".strip() or user.username

        return Response(
            {"id": user.id, "email": user.email, "fullname": fullname},
            status=status.HTTP_200_OK,
        )
