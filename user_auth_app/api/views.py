from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import RegistrationSerializer, LoginSerializer
from rest_framework.throttling import ScopedRateThrottle

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
    """
    Login per E-Mail + Passwort (DRF TokenAuth).
    Request:
      { "email": "...", "password": "..." }
    Response (200):
      { "token": "...", "fullname": "...", "email": "...", "user_id": ... }
    """
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
