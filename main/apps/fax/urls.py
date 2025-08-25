from django.urls import path
from .views import (
    SendFaxView,
    UploadFaxFileView,
    FaxStatusView,
    FaxListView,
    InboundFaxWebhookView
)

app_name = 'fax'

urlpatterns = [
    path('send/', SendFaxView.as_view(), name='send-fax'),
    path('upload/', UploadFaxFileView.as_view(), name='upload-file'),
    path('status/<uuid:uuid>/', FaxStatusView.as_view(), name='fax-status'),
    path('list/', FaxListView.as_view(), name='fax-list'),
    path('webhook/inbound/', InboundFaxWebhookView.as_view(), name='inbound-webhook'),
]