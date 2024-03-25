import os
import elasticsearch
from elasticsearch import Elasticsearch, RequestsHttpConnection, exceptions
from datetime import datetime, timezone
from requests_aws4auth import AWS4Auth

from .error.exceptions import *


class Elastic(elasticsearch.Elasticsearch):

    def __init__(self):

        if os.environ.get('ENV') == 'PROD':

            awsauth                                     = AWS4Auth(
                                                            os.environ.get("AWS_ACCESS_KEY_ID"),
                                                            os.environ.get("AWS_SECRET_ACCESS_KEY"),
                                                            os.environ.get("AWS_REGION"),
                                                            'es'
                                                        )

            self.es                                     = Elasticsearch(
                                                            os.environ.get("ELASTIC_SERVER"),
                                                            http_auth=awsauth,
                                                            use_ssl=True,
                                                            verify_certs=True,
                                                            connection_class=RequestsHttpConnection,
                                                            timeout=30,
                                                            max_retries=10,
                                                            retry_on_timeout=True
                                                        )

        else:

            self.es                                     = Elasticsearch(
                                                            os.environ.get("ELASTIC_SERVER"),
                                                            http_auth=(
                                                                os.environ.get("OPENSEARCH_USER"),
                                                                os.environ.get("OPENSEARCH_PASS"),
                                                            ),
                                                            scheme="https",
                                                            port=os.environ.get("OPENSEARCH_PORT", 9200),
                                                            verify_certs=False,
                                                        )

            self.user = 'ms-process-faceid'
            self.profile_driver_faceid = 'profile_driver_faceid'


    def build_query(self, include_fields: list = [], sort_by: dict = {}, **kwargs) -> dict:
        query = {
            'query': {
                'bool': {
                    'must': [
                        {'match': {'s_record_status': 'ACTIVE'}}
                    ]
                }
            }, "size": 10000
        }
        if include_fields:
            query['_source'] = {'includes': include_fields}

        if sort_by:
            query['sort'] = []
            for key, order in sort_by.items():
                query['sort'].append(
                    {key: {'order': order}}
                )
        for key, value in kwargs.items():
            if value is None:
                continue
            query['query']['bool']['must'].append({'match': {key : value}})

        return query
    
    def query_elastic(self, index: str, query: dict) -> list:
        
        parsed_docs = []
        raw_docs = self.es.search(index=index, body=query)['hits']['hits']
        for doc in raw_docs:
            data = doc['_source']
            data['doc_id'] = doc['_id']
            parsed_docs.append(data)
  
        return parsed_docs
    
    def retorna_profile_driver_faceid(self, operation_hash: str, driver_hash: str) -> dict:
        query = self.build_query(
            pk_operation_hash=operation_hash, pk_driver_hash=driver_hash
        )
        query['size']= 1
        raw_docs = self.query_elastic('profile_driver_faceid', query=query)
        return raw_docs[0] if raw_docs else {}
    
    def retorna_profile_driver(self, operation_hash: str, driver_hash: str) -> dict:
        query = self.build_query(
            pk_operation_hash=operation_hash, pk_driver_hash=driver_hash
        )
        query['size']= 1
        raw_docs = self.query_elastic('profile_driver', query=query)
        return raw_docs[0] if raw_docs else {}
    
    def retorna_company_operation(self, operation_hash: str) -> dict:
        query = self.build_query(
            pk_operation_hash=operation_hash
        )
        query['size']= 1
        raw_docs = self.query_elastic('company_operation', query=query)
        return raw_docs[0] if raw_docs else {}

    def grava_elastic(self, arg_index: str, arg_body: dict) -> dict:
        ''' Atualiza campos de status e então grava registro no Elastic '''
        arg_body['s_record_status'] = 'ACTIVE'
        arg_body['s_record_creation_date'] = datetime.now(timezone.utc)
        arg_body['s_record_created_by_user'] = 'ms-process-faceid'
        
        return self.es.index(index = arg_index, refresh = True, body = arg_body)

    def atualiza_elastic(self, arg_index: str, arg_doc_id: str, arg_body: dict) -> dict:
        ''' Atualiza campos de status e então atualiza registro no Elastic '''
        arg_body['s_record_last_update'] = datetime.now(timezone.utc)
        arg_body['s_record_updated_by_user'] = 'ms-process-faceid'
        new_event_request_body = {"doc": arg_body}

        return self.es.update(index = arg_index, id = arg_doc_id, refresh = True, body = new_event_request_body)
