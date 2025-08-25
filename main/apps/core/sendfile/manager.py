from .audio import Audio
from .fax_simple import FaxSimple
from ..vars import GATEWAY_PREFIX

class Manager(object):

	def __init__(self, service, username, file_path, numbers):
		self.service = service
		self.username = username
		self.file_path = file_path
		self.numbers = numbers
		self.name = GATEWAY_PREFIX + self.username

	def execute(self):
		body = ""
		if self.service == "audio":
			am = Audio(self.name, self.username, self.file_path, self.numbers)
			body = am.execute()
		elif self.service == "fax":
			# Use simplified fax handler without CDR pusher
			fm = FaxSimple(self.username, self.file_path, self.numbers)
			body = fm.execute()
		return body
