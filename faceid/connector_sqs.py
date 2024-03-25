import os
import json
import logging

# from flask_api import FlaskAPI

# from flask_api import status

import boto3
import uuid

# app = FlaskAPI(__name__)


class QueueConnector ():

    def __init__(self, **kwargs):
        logging.basicConfig(level=logging.DEBUG)
        session = boto3.Session(
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        self.sqsResource = boto3.resource(
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION'),
            service_name='sqs'
        )
        self.sqsClient = session.client('sqs')

        self.ret_api_create = {
            "request_type": None,  # API Description
            "api_message": None,  # API MESSAGE ( SUCESS / ERROR )
            "api_response": None,  # API RESPONSE LOG
        }

    def get_status(self):
        """Get Queue status

        Returns:
            json: when validation succeeds, we yield status = active
        """

        # logging.error("Entrou no _get_status")

        try:
            resp = {
                'status': None,
                'status_code': None
            }
            if self.sqsClient.list_queues():
                # logging.error("OK")
                your_value = os.environ.get('ENV')
                resp = {'environment': your_value, 'status': 'active'}
            else:
                # logging.error("NOK")
                resp['status'] = 'Error'
            return resp
        except Exception as e:
            resp['status'] = 'Error'
            if not resp['status_code']:
                resp['status_code'] = 500
            logging.error(e)
            return resp, status.HTTP_500_INTERNAL_SERVER_ERROR

    def insert_queue(self, queue_name, body=None):
        """Set message to Queue

        Returns:
            json: when validation succeeds, we yield status = inserted
        """

        # logging.error("Entrou no _get_status")

        try:
            resp = {
                'status': None,
                'status_code': None
            }

            # Get the queue
            queue = self.sqsResource.get_queue_by_name(QueueName=queue_name)

            # Create a new message
            response = queue.send_message(
                MessageBody=json.dumps(body, default=str))

            # logging.error("OK")
            # logging.error(response)

            if response:
                self.ret_api_create["api_message"] = "Document queued "\
                                                     "successfuly"
                self.ret_api_create["request_type"] = "Queue Insert"
                self.ret_api_create["api_response"] = {
                    "status": "OK",
                    "status_code": 200,
                    "is_success": True
                }
                return self.ret_api_create
            else:
                # logging.error("NOK")
                resp['status'] = 'Error'
            return resp
        except Exception as e:
            resp['status'] = 'Error'
            if not resp['status_code']:
                resp['status_code'] = 500
            logging.error(e)
            return resp #, status.HTTP_500_INTERNAL_SERVER_ERROR

    def insert_queue_fifo(self, queue_name, body=None):
        """Set message to Queue

        Returns:
            json: when validation succeeds, we yield status = inserted
        """

        # logging.error("Entrou no _get_status")

        resp = {
            'status': None,
            'status_code': None
        }

        try:
            # Get the queue
            queue = self.sqsResource.get_queue_by_name(QueueName=queue_name)

            # Create a new message
            _id = str(uuid.uuid4())
            response = queue.send_message(MessageBody=json.dumps(
                body, default=str), MessageGroupId='MsgGrId', MessageDeduplicationId=_id)

            # logging.error("OK")
            # logging.error(response)

            if response:
                self.ret_api_create["api_message"] = "Document queued "\
                                                     "successfuly"
                self.ret_api_create["request_type"] = "Queue Insert"
                self.ret_api_create["api_response"] = {
                    "status": "OK",
                    "status_code": 200,
                    "is_success": True
                }
                return self.ret_api_create
            else:
                # logging.error("NOK")
                resp['status'] = 'Error'
            return resp
        except Exception as e:
            resp['status'] = 'Error'
            if not resp['status_code']:
                resp['status_code'] = 500
            logging.error(e)
            return resp #, status.HTTP_500_INTERNAL_SERVER_ERROR


    def retrieve_queue(self, queue_name):
        """Get message from Queue

        Returns:
            json: when validation succeeds, we yield status = inserted
        """

        # logging.error("Entrou no _get_status")

        try:
            resp = {
                'status': None,
                'status_code': None
            }

            # Get the queue
            queue = self.sqsResource.get_queue_by_name(QueueName=queue_name)

            queueResponse = None
            # Retrieving message
            # logging.error(queue.receive_messages(MaxNumberOfMessages=1))

            consult = queue.receive_messages(MaxNumberOfMessages=1)

            if len(consult) > 0:
                for message in consult:
                    # logging.error("MSG RECEIVED {}".format(message.body))
                    queueResponse = message.body
                    message.delete()

            if queueResponse:
                self.ret_api_create["api_message"] = "Document queued "\
                                                     "successfuly"
                self.ret_api_create["request_type"] = "Queue Insert"
                self.ret_api_create["api_response"] = {
                    "status": "OK",
                    "status_code": 200,
                    "is_success": True,
                    "message": json.loads(queueResponse)

                }
                return self.ret_api_create
            else:
                resp['status'] = 'Error'
            return resp
        except Exception as e:
            resp['status'] = 'Error'
            if not resp['status_code']:
                resp['status_code'] = 500
            logging.error(e)
            return resp
