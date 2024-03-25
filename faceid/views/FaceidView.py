
import face_recognition 
import numpy as np 
import os
import logging
import cv2
import base64
import base64
import urllib.request as ur
from flask_api import status

from flask_cors import CORS
from flask import request, jsonify
from flask_api import FlaskAPI

from ..helpers.tools import Toolbox, MapTools
from ..elastic import Elastic
from ..connector_sqs import QueueConnector


class FaceidView:

    def __init__(self):
        self.user = 'ms-process-faceid'
        self.Toolbox = Toolbox()
        self.MapTools = MapTools(self.Toolbox)
        self.api_aws_sqs = QueueConnector()
        self.es = Elastic()
        self.maps_api_url = os.environ.get("MAPS_API_URL")
        self.headers = {"Content-Type": "application/json"}

    #---------------------------------------------------------------------------------------------
    # FACE_ENCODING
    #---------------------------------------------------------------------------------------------

    def face_encoding_create( self, arg_json ):

        logging.info('Iniciando processo de encoding create')

        # try:
            
        driver_hash = arg_json.get("pk_driver_hash")
        operation_hash = arg_json.get('pk_operation_hash')
        economic_group_hash = arg_json.get("pk_economic_group_hash")
        subsidiary_hash = arg_json.get("pk_subsidiary_hash")
        image = arg_json.get("image")

        #---------------------------------------------------------------------------------------------
        # Search profile driver for saveing doc
        #---------------------------------------------------------------------------------------------
        result_profile = self.es.retorna_profile_driver_faceid(operation_hash, driver_hash)
        
        #---------------------------------------------------------------------------------------------
        # Transform base64 to imagem format RB
        #---------------------------------------------------------------------------------------------
        logging.info('Transformando base64, girando e reajustando tamanho')
        image_utf8 = image.encode("utf-8")

        with open(f"{driver_hash}.png", "wb") as fh:
            fh.write(base64.decodebytes(image_utf8))

        image_path = (f'{driver_hash}.png')

        image_load = face_recognition.load_image_file(image_path)
        image_final = cv2.cvtColor(image_load, cv2.COLOR_BGR2RGB)
        os.remove(f'{driver_hash}.png')

        #---------------------------------------------------------------------------------------------
        # Resize image
        #---------------------------------------------------------------------------------------------       
        image_final = cv2.resize(image_final, (720, 1280))

        #---------------------------------------------------------------------------------------------
        # Detect the faces from the image
        #---------------------------------------------------------------------------------------------
        logging.info('Detectando rosto')
        face_locations = face_recognition.face_locations(image_final)[0]
        
        #---------------------------------------------------------------------------------------------
        # Create rectangle on face 
        #---------------------------------------------------------------------------------------------
        logging.info('Gerando retangulo na região do rosto encontrado')
        cv2.rectangle(image_final,(face_locations[3], face_locations[0]), (face_locations[1], face_locations[2]),(0, 255,0), 2)

        #---------------------------------------------------------------------------------------------
        # Encode the 128-dimension face encoding for each face in the image 
        #---------------------------------------------------------------------------------------------
        logging.info('Gerando linhas no rosto encontrado')
        face_encodings = face_recognition.face_encodings(image_final)[0]

        list_encoding = [face_encoding.tolist() for face_encoding in face_encodings]
        ret_json = {
            'pk_subsidiary_hash': subsidiary_hash,
            'pk_economic_group_hash': economic_group_hash,
            'pk_operation_hash': operation_hash,
            'pk_driver_hash': driver_hash,
            'faceid_success': 'success',
            'driver_total_faces': len(face_locations),
            'driver_face_locations': face_locations,
            'driver_face_id_encoding': list_encoding
        }
        logging.info('Gravando dados')

        #---------------------------------------------------------------------------------------------
        # Check if exist profile driver in elastic or not
        #---------------------------------------------------------------------------------------------
        logging.info('Verificando se já existe registros de fotos do motorista!')
        if result_profile:
            logging.info('Atualizando documento!')
            doc_id = result_profile.get('doc_id')
            self.es.atualiza_elastic('profile_driver_faceid', doc_id, ret_json)

        else:
            logging.info('Criando um novo documento!')
            self.es.grava_elastic('profile_driver_faceid', ret_json)

        logging.info('Finalizando...')
        return {'status': 'OK'}, status.HTTP_200_OK
        
        # except Exception as e:
        #     logging.error('Error ao registrar a foto!')
        #     return {'status': 'Erro' }, status.HTTP_404_NOT_FOUND
    
    #---------------------------------------------------------------------------------------------
    # FACE_SEARCH
    #---------------------------------------------------------------------------------------------
    def search_faceid( self, arg_json ):

        logging.info('Iniciando processo de comparação de rostos...')

        # try:

        driver_hash = arg_json.get("pk_driver_hash")
        operation_hash = arg_json.get("pk_operation_hash")
        image = arg_json.get("image")
        front_cam = arg_json.get('is_camera')

        #---------------------------------------------------------------------------------------------
        # Search profile driver for saveing doc
        #---------------------------------------------------------------------------------------------
        resultado = self.es.retorna_profile_driver_faceid(operation_hash, driver_hash)
        points = resultado.get('driver_face_id_encoding')

        #---------------------------------------------------------------------------------------------
        # Detect the faces from the images
        #---------------------------------------------------------------------------------------------
        logging.info('Transformando base64, girando e reajustando tamanho')
        image = image.encode("utf-8")

        with open(f"{driver_hash}.png", "wb") as fh:
            fh.write(base64.decodebytes(image))

        image = (f'{driver_hash}.png')

        #---------------------------------------------------------------------------------------------
        # Encode the 128-dimension face encoding for each face in the image 
        #---------------------------------------------------------------------------------------------
        logging.info('Gerando linhas no rosto de comparação')
        ret_face_encoding = self.face_encoding(image, driver_hash, front_cam)
        ret_face_elastic = np.array(points)

        #---------------------------------------------------------------------------------------------
        # Compare the faces currenty and faces saved in elastic
        #---------------------------------------------------------------------------------------------
        logging.info('Comparando rostos...')
        return_faceid = face_recognition.compare_faces([ret_face_elastic], ret_face_encoding, tolerance=0.6)
        accurracy_face_id = face_recognition.face_distance([ret_face_elastic], ret_face_encoding)

        #---------------------------------------------------------------------------------------------
        # Return result accurracy face for face
        #---------------------------------------------------------------------------------------------
        logging.info(f'Rotos comparados, acurácia de: {return_faceid[0], float(accurracy_face_id)}')
        if return_faceid[0] == True and float(accurracy_face_id) <= 0.56:
            logging.info(f'Motorista encontrado e aceito!')
            return {'success': True}, status.HTTP_200_OK
        else:
            logging.info(f'Motorista não encontrado e negado!')
            return {'success': False}, status.HTTP_404_NOT_FOUND

        # except Exception as e:
        #     logging.error('Error ao comparar a foto!')
        #     return {'success': False }, status.HTTP_404_NOT_FOUND
        
    
    def face_encoding( self, files, driver_hash, front_cam ):
        
        image = face_recognition.load_image_file(files)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        os.remove(f'{driver_hash}.png')
        
        logging.info('Transformando base64, girando e reajustando tamanho')
        #---------------------------------------------------------------------------------------------
        # Rotate image and resize
        #---------------------------------------------------------------------------------------------
        if front_cam is True:
            img_v = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            img_v = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        
        image_final = cv2.resize(img_v, (720, 1280))

        #---------------------------------------------------------------------------------------------
        # Detect the faces from the images
        #---------------------------------------------------------------------------------------------
        logging.info('Detectando rosto')
        face_locations = face_recognition.face_locations(image_final)[0]
    
        #---------------------------------------------------------------------------------------------
        # Generate rectangle green on face the people
        #---------------------------------------------------------------------------------------------
        logging.info('Gerando retangulo na região do rosto encontrada')
        cv2.rectangle(image_final,(face_locations[3], face_locations[0]), (face_locations[1], face_locations[2]),(0, 255,0), 2)

        #---------------------------------------------------------------------------------------------
        # Encode the 128-dimension face encoding for each face in the image 
        #---------------------------------------------------------------------------------------------
        logging.info('Gerando linhas no rosto encontrado')
        face_encodings = face_recognition.face_encodings(image_final)[0]

        return face_encodings
    
    def faceid_unic_authentication(self, arg_json):

        image = arg_json.get("image")
        front_cam = arg_json.get('is_camera')

        #---------------------------------------------------------------------------------------------
        # Detect the faces from the images
        #---------------------------------------------------------------------------------------------
        logging.info('Transformando base64, girando e reajustando tamanho')
        image = image.encode("utf-8")

        with open(f"driver.png", "wb") as fh:
            fh.write(base64.decodebytes(image))
        
        image_path = (f'driver.png')

        image_load = face_recognition.load_image_file(image_path)
        image = cv2.cvtColor(image_load, cv2.COLOR_BGR2RGB)

        #---------------------------------------------------------------------------------------------
        # Rotate image and resize
        #---------------------------------------------------------------------------------------------
        logging.info('Rotacionando imagem e redimencionando')
        if front_cam is True:
            img_v = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            img_v = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        
        image_final = cv2.resize(img_v, (720, 1280))
        os.remove(f'driver.png')

        #---------------------------------------------------------------------------------------------
        # Detect the faces from the images
        #---------------------------------------------------------------------------------------------
        logging.info('Detectando rosto')
        face_locations = face_recognition.face_locations(image_final)[0]
    
        #---------------------------------------------------------------------------------------------
        # Generate rectangle green on face the people
        #---------------------------------------------------------------------------------------------
        logging.info('Gerando retangulo na região do rosto encontrada')
        cv2.rectangle(image_final,(face_locations[3], face_locations[0]), (face_locations[1], face_locations[2]),(0, 255,0), 2)

        #---------------------------------------------------------------------------------------------
        # Encode the 128-dimension face encoding for each face in the image 
        #---------------------------------------------------------------------------------------------
        logging.info('Gerando linhas no rosto encontrado')
        face_encodings = face_recognition.face_encodings(image_final)[0]

        #---------------------------------------------------------------------------------------------
        # Compare the faces currenty and faces saved in elastic
        #---------------------------------------------------------------------------------------------
        logging.info('Buscando dados das faces no elastic')
        drivers = self.es.query_elastic('profile_driver_faceid', query=self.es.build_query(sort_by={'s_record_creation_date': 'desc'}))
        faceid_identify = []

        for driver in drivers:
            points = driver.get('driver_face_id_encoding')
            ret_face_elastic = np.array(points)

            #---------------------------------------------------------------------------------------------
            # Compare the faces currenty and faces saved in elastic
            #---------------------------------------------------------------------------------------------
            logging.info('Comparando rostos...')
            return_faceid = face_recognition.compare_faces([ret_face_elastic], face_encodings, tolerance=0.6)
            accurracy_face_id = face_recognition.face_distance([ret_face_elastic], face_encodings)

            #---------------------------------------------------------------------------------------------
            # Return result accurracy face for face
            #---------------------------------------------------------------------------------------------
            logging.info(f'Rostos comparados, acurácia de: {return_faceid[0], float(accurracy_face_id)}')
            if return_faceid[0] == True and float(accurracy_face_id) <= 0.55:
                faceid_identify.append((driver, float(accurracy_face_id)))
            
        if faceid_identify:
            #---------------------------------------------------------------------------------------------
            # Search the min accurracy face for face
            #---------------------------------------------------------------------------------------------
            logging.info(f'Separando motoristas parecidos')
            min_accurracy = min(faceid_identify, key=lambda x: x[1])
            min_driver = min_accurracy[0]

            logging.info(f'Motorista aceito com acurácia {min_accurracy[1]}')

            driver_hash = min_driver.get('pk_driver_hash')
            operation_hash = min_driver.get('pk_operation_hash')

            #---------------------------------------------------------------------------------------------
            # Search data to profile_driver and company_operation
            #---------------------------------------------------------------------------------------------
            resultado_driver = self.es.retorna_profile_driver(operation_hash, driver_hash)
            resultado_company = self.es.retorna_company_operation(operation_hash)

            payload = {
                "pk_economic_group_hash": resultado_driver.get('pk_economic_group_hash'),
                "pk_operation_hash": operation_hash,
                "pk_driver_hash": driver_hash,
                "federal_id": resultado_driver.get('federal_id'),
                "full_name": resultado_driver.get('full_name'),
                "operation_name": resultado_company.get('operation_name')
            }

            logging.info(f'Dados do motorista encontrado: {payload}')

            return {"payload": payload}, status.HTTP_200_OK

        logging.info(f'Motorista não encontrado e negado!')
        return {'success': False}, status.HTTP_404_NOT_FOUND

    def face_encoding_delete(self, arg_json):

        driver_hash = arg_json.get("pk_driver_hash")
        opereation_hash = arg_json.get('pk_operation_hash')

        resultado = self.es.retorna_profile_driver_faceid(opereation_hash, driver_hash)

        doc_id = resultado.get("doc_id")

        ret_json = {
                's_record_status': "DELETED",
            }
        
        self.es.atualiza_elastic('profile_driver_faceid', doc_id, ret_json)

        return {'success': True}, status.HTTP_200_OK


