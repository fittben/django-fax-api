from rest_framework import serializers
from .models import FaxTransaction, FaxQueue

class FaxTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaxTransaction
        fields = '__all__'
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'user']


class FaxQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaxQueue
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SendFaxSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text="Sender's phone number")
    filename = serializers.CharField(required=True, help_text="File to send")
    numbers = serializers.CharField(required=True, help_text="Recipient numbers (comma-separated)")
    is_enhanced = serializers.BooleanField(required=False, default=False, help_text="Use enhanced fax quality")


class FaxStatusSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(required=True, help_text="Fax transaction UUID")