class GenericError:

	def __init__(self, code: str, type: str):
		self.code = code
		self.type = type

	def to_json(self) -> dict:
		return {
			'error_code': self.code,
			'error_type': self.type
		}


class Error:

	REQUIRED_FIELD = GenericError(400, 'required_field')
	INVALID_TYPE = GenericError(400, 'invalid_type')
	DUPLICATED_FIELD = GenericError(409, 'duplicated_field')
	INVALID_DATE = GenericError(400, 'invalid_date')
	INVALID_DOC = GenericError(400, 'invalid_doc')
	NOT_ALPHANUMERIC = GenericError(400, 'not_alphanumeric')
	INVALID_LOCATION = GenericError(400, 'invalid_location')