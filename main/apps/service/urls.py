from django.urls import include, path
from .views.voice import OriginateVoice
from .views.fax import OriginateFax
from .views.fax_report import FaxReport
from .views.fax_inbox import FaxInbox
from .views.file import UploadFile, DownloadFile
from .views.root import APIServiceView, APIVoiceView, APIFileView, APIFaxView

urlpatterns = [
	path('', APIServiceView.as_view(), name="service"),
	path('voice/', APIVoiceView.as_view(), name="voice"),
	path('voice/originate/', OriginateVoice.as_view(), name="voice_originate"),
	
	path('file/', APIFileView.as_view(), name="file"),
	path('file/upload/', UploadFile.as_view(), name="file_upload"),
	path('file/download/', DownloadFile.as_view(), name="file_download"),

	path('fax/', APIFaxView.as_view(), name="fax"),
	path('fax/originate/', OriginateFax.as_view(), name="fax_originate"),
	path('fax/report/', FaxReport.as_view(), name="fax_report"),
	path('fax/inbox/', FaxInbox.as_view(), name="fax_inbox"),
]