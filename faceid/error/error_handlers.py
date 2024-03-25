import elasticsearch
import logging
import traceback
import os
from flask import jsonify
from flask_api import status, FlaskAPI
from werkzeug.exceptions import NotFound

from connector_sqs import QueueConnector
from .exceptions import *
from constants import ALERT_TYPE_TRACEBACK_ERROR, ALERT_SEVERITY_HIGHEST


def gera_alerta_de_traceback(exception: Exception, traceback_message: str):
    arg_json = exception.payload if hasattr(exception, "payload") else {}

    json_alerta_traceback = {}
    json_alerta_traceback['pk_economic_group_hash']            = arg_json.get('pk_economic_group_hash')
    json_alerta_traceback['pk_subsidiary_hash']                = arg_json.get('pk_subsidiary_hash')
    json_alerta_traceback['pk_operation_hash']                 = arg_json.get('pk_operation_hash')
    json_alerta_traceback['vehicle_hash']                      = arg_json.get('vehicle_hash')
    json_alerta_traceback['license_plate']                     = arg_json.get('vehicle_license_plate')
    json_alerta_traceback['id_veiculo']                        = None
    json_alerta_traceback['timeline_hash']                     = arg_json.get('pk_timeline_hash')
    json_alerta_traceback['alert_category']                    = 'evi_system'
    json_alerta_traceback['alert_type']                        = ALERT_TYPE_TRACEBACK_ERROR
    json_alerta_traceback['alert_severity']                    = ALERT_SEVERITY_HIGHEST
    json_alerta_traceback['alert_message']                     = ALERT_TYPE_TRACEBACK_ERROR
    json_alerta_traceback['alert_response_description']        = traceback_message
    json_alerta_traceback['ms_name']                           = os.environ.get('MS_NAME', 'ms-process-reorder-route-node')
    json_alerta_traceback['telemetry_json']                    = arg_json

    # QueueConnector().insert_queue_fifo(os.environ.get("QUEUE_SEND_ALERTS_TRACEBACK"), json_alerta_traceback)
    logging.debug('ENVIANDO PARA FILA send-alerts.fifo')
    logging.debug('ENVIADO COM SUCESSO')

 

class Error:
    def __init__(self, code, description):
        self.code = code
        self.description = description

    def to_json(self):
        return jsonify(
            [{"error_code": self.code, "error_description": self.description}]
        )


def register_error_handlers(app: FlaskAPI):

    def handle_invalid_field_error(err: InvalidFieldException):
        logging.debug(err.args)
        return err.to_json(), status.HTTP_400_BAD_REQUEST

    app.register_error_handler(InvalidFieldException, handle_invalid_field_error)

    def handle_elastic_404_error(err: PKNotFoundError):
        # Ocorre quando os nodes de uma timeline não são encontrados
        # Qd isso acontece, workflow deve cancelar o processamento da telemetria.
        # Deve gerar alerta de traceback?
        return err.to_json(), status.HTTP_404_NOT_FOUND

    app.register_error_handler(PKNotFoundError, handle_elastic_404_error)

    def handle_elasticsearch_error(err: elasticsearch.exceptions.RequestError):
        logging.debug(err.args[2]["error"]["root_cause"])
        error = err.args[2]["error"]["root_cause"][0]
        return (
            Error(error["type"], error["reason"]).to_json(),
            status.HTTP_400_BAD_REQUEST,
        )
    app.register_error_handler(
        elasticsearch.exceptions.RequestError, handle_elasticsearch_error
    )

    def handle_elastic_offline_error(err: elasticsearch.exceptions.ConnectionError):
        logging.exception(err.error)
        return jsonify(message=err.error), status.HTTP_400_BAD_REQUEST

    app.register_error_handler(
        elasticsearch.exceptions.ConnectionError, handle_elasticsearch_error
    )

    def handle_generic(err: Exception):
        # Ocorreu exceção
        traceback_str = traceback.format_exc()
        logging.exception(traceback_str)
        gera_alerta_de_traceback(err, traceback_str)
        return jsonify(message=traceback_str, error_description=traceback_str), status.HTTP_500_INTERNAL_SERVER_ERROR

    app.register_error_handler(Exception, handle_generic)
