from flask import jsonify
from .enums import Error



class EviException(Exception):

	def __init__(self, msg: str, data: dict, error: Error):
		self.message = msg
		self.payload = data
		self.error = error
		super().__init__(self.message)

	def to_json(self, do_jsonify: bool = True) -> dict:
		excp_data = {
			'error_code': self.error.code,
			'error_type': self.error.type,
			'error_description': self.message,
			'payload': self.payload
		}
		return jsonify(excp_data) if do_jsonify else excp_data



class InvalidFieldException(EviException):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)



class PKNotFoundError(EviException):

	def __init__(self, pk: str, id: str, payload: dict):
		self.pk = pk
		self.id = id
		message = f"Document {pk}={id!r} not found!"
		super().__init__(message, payload, Error.INVALID_DOC)

	def to_json(self) -> dict:
		data = super().to_json(do_jsonify=False)
		data['pk'] = self.pk
		data['id'] = self.id
		return jsonify(data)


class ConnectionError(Exception):

	def __init__(self, msg):
		super().__init__(msg)