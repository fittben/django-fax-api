from django.urls import include, path
from .views.operation import GatewayOperation
from .views.check import GatewayCheck
from .views.root import APIGatewayView

urlpatterns = [
	path('', APIGatewayView.as_view(), name="gateway"),
	path('operation/', GatewayOperation.as_view(), name="operation"), #POST
	path('check/', GatewayCheck.as_view(), name="check"),
]