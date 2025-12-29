from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions

from .serializers import OperatorRegisterSerializer, OperatorLoginSerializer, SupplierProfileSerializer

from rest_framework.decorators import action

from .models import SupplierProfile
from .permissions import IsOperator, IsVerifiedOperator, IsOwnerOrAdmin

from rest_framework.parsers import MultiPartParser, FormParser




def index(request):
    return HttpResponse("Hello, this is the Users app homepage!")


class OperatorRegisterView(APIView):
    """
    POST /api/users/operators/signup/
    Register a new operator (requires phone_number).
    Account stays inactive until admin verifies.
    """
    def post(self, request):
        serializer = OperatorRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Operator registered successfully. Awaiting admin approval.",
                "operator": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_verified": user.is_verified,
                    "phone_number": user.phone_number
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OperatorLoginView(APIView):
    """
    POST /api/users/operators/login/
    Login with email + password. Returns JWT tokens if verified.
    """
    def post(self, request):
        serializer = OperatorLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                "message": "Login successful.",
                "access": serializer.validated_data['access'],
                "refresh": serializer.validated_data['refresh'],
                "operator": serializer.validated_data['user']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SupplierProfileViewSet(viewsets.ModelViewSet):
    queryset = SupplierProfile.objects.all()
    serializer_class = SupplierProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOperator, IsOwnerOrAdmin]
    parser_classes = (MultiPartParser, FormParser)  # <-- enables file uploads

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsOperator(), IsVerifiedOperator()]
        elif self.action == 'list':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        else:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return SupplierProfile.objects.all()
        return SupplierProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get', 'patch', 'put'], url_path='me')
    def me(self, request):
        """
        GET  /api/users/operators/profile/me/
        PATCH/PUT  /api/users/operators/profile/me/  
        """
        try:
            profile = SupplierProfile.objects.get(user=request.user)
        except SupplierProfile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method in ['PATCH', 'PUT']:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(profile)
        return Response(serializer.data)
