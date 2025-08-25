from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid

from .models import FaxTransaction, FaxQueue
from .serializers import (
    FaxTransactionSerializer, 
    SendFaxSerializer, 
    FaxStatusSerializer
)
from .fax_handler import FaxHandler
from main.apps.core.vars import TXFAX_DIR, RXFAX_DIR


class SendFaxView(APIView):
    """
    Send fax to one or multiple recipients
    
    Example:
    ```
    curl -X POST http://127.0.0.1:8000/api/fax/send/ \
         -H 'Authorization: Token YOUR_TOKEN' \
         -H 'Content-Type: application/json' \
         -d '{
            "username": "908509999999",
            "filename": "document.pdf",
            "numbers": "05319999999,05329999999",
            "is_enhanced": false
         }'
    ```
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SendFaxSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        handler = FaxHandler()
        
        result = handler.send_fax(
            username=data['username'],
            file_path=data['filename'],
            numbers=data['numbers'],
            is_enhanced=data.get('is_enhanced', False),
            user=request.user
        )
        
        if result['success']:
            return Response({
                'status': 'OK',
                'code': 200,
                'uuid': str(result['transaction'].uuid),
                'message': result['message'],
                'details': result['details']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'Error',
                'code': 400,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


class UploadFaxFileView(APIView):
    """
    Upload a file for fax transmission
    
    Example:
    ```
    curl -X POST http://127.0.0.1:8000/api/fax/upload/ \
         -H 'Authorization: Token YOUR_TOKEN' \
         -F 'file=@/path/to/document.pdf'
    ```
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        
        # Generate unique filename
        file_extension = os.path.splitext(file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Save file to TXFAX_DIR
        file_path = os.path.join(TXFAX_DIR, unique_filename)
        
        # Ensure directory exists
        os.makedirs(TXFAX_DIR, exist_ok=True)
        
        # Save file
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        return Response({
            'status': 'OK',
            'filename': unique_filename,
            'original_name': file.name,
            'size': file.size
        }, status=status.HTTP_201_CREATED)


class FaxStatusView(APIView):
    """
    Get status of a fax transaction
    
    Example:
    ```
    curl -X GET http://127.0.0.1:8000/api/fax/status/UUID/ \
         -H 'Authorization: Token YOUR_TOKEN'
    ```
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, uuid=None):
        if not uuid:
            return Response(
                {'error': 'UUID required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        handler = FaxHandler()
        status_info = handler.get_fax_status(uuid)
        
        if status_info:
            return Response(status_info, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FaxListView(APIView):
    """
    List all fax transactions for the authenticated user
    
    Example:
    ```
    curl -X GET http://127.0.0.1:8000/api/fax/list/ \
         -H 'Authorization: Token YOUR_TOKEN'
    ```
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get query parameters
        direction = request.query_params.get('direction', None)
        status_filter = request.query_params.get('status', None)
        
        # Build query
        queryset = FaxTransaction.objects.all()
        
        if request.user and not request.user.is_staff:
            queryset = queryset.filter(user=request.user)
        
        if direction:
            queryset = queryset.filter(direction=direction)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Serialize and return
        serializer = FaxTransactionSerializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class InboundFaxWebhookView(APIView):
    """
    Webhook endpoint for receiving inbound fax notifications from FreeSWITCH
    """
    authentication_classes = []  # No auth for webhook
    permission_classes = []
    
    def post(self, request):
        # Extract fax information from request
        caller_number = request.data.get('caller_id_number', 'Unknown')
        called_number = request.data.get('destination_number', 'Unknown')
        file_name = request.data.get('fax_file', None)
        
        if not file_name:
            return Response(
                {'error': 'No fax file specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_path = os.path.join(RXFAX_DIR, file_name)
        
        # Create transaction record
        handler = FaxHandler()
        transaction = handler.receive_fax(
            caller_number=caller_number,
            called_number=called_number,
            file_path=file_path
        )
        
        return Response({
            'status': 'OK',
            'uuid': str(transaction.uuid)
        }, status=status.HTTP_200_OK)