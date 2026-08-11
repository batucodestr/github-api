from django.shortcuts import render
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserDetailSerializer, LoginSerializer, SignUpSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer, TokenVerifySerializer
from .tokens import get_tokens_for_user
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser


User = get_user_model()

@extend_schema(
    tags=['Kullanıcılar'],
    summary='JWT erişim ve yenileme tokenleri alır',
    description='E-posta ve şifre ile giriş yaparak `access` (1 saat) ve `refresh` (7 gün) token çifti döndürür.',
)
class CustomTokenObtainPairView(TokenObtainPairView):
    pass

@extend_schema(tags=['Kullanıcılar'], summary='JWT erişim tokenini yeniler')
class CustomTokenRefreshView(TokenRefreshView):
    pass

@extend_schema(tags=['Kullanıcılar'], summary='JWT tokenini doğrular')
class CustomTokenVerifyView(TokenVerifyView):
    pass

@extend_schema(
    tags=['Kullanıcılar'],
    summary='Yeni bir kullanıcı kaydı oluşturur',
    description='Yeni bir kullanıcı hesabı oluşturur ve kullanıcı bilgileriyle birlikte JWT token çifti döndürür.',
)
class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_tokens_for_user(user)

        response = {
            'user': UserDetailSerializer(user, context=self.get_serializer_context()).data,
            'refresh': token['refresh'],
            'access': token['access'],
        }

        return Response(data=response, status=status.HTTP_201_CREATED)

@extend_schema(
    tags=['Kullanıcılar'],
    summary='Kullanıcıyı doğrular ve JWT token döndürür',
    description='E-posta ve şifre ile kimlik doğrulama yapar, başarılı olursa `access`/`refresh` token döndürür.',
    request=LoginSerializer,
)
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)

        if user is not None:
            token = get_tokens_for_user(user)
            response = {
                'message': 'Login successful',
                'refresh': token['refresh'],
                'access': token['access'],
            }
            return Response(data=response, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(tags=['Kullanıcılar'], summary='Yönetici için tüm kullanıcıları listeler')
class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Kullanıcılar'], summary='Yönetici için belirli bir kullanıcının detaylarını getirir')
class AdminUserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminUser]


