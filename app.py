import logging
from flask_cors import CORS
from flask import request, jsonify
from flask import Flask
from flask import Flask, request

from faceid.helpers.tools import load_json
from faceid.views.FaceidView import FaceidView
from faceid.error.error_handlers import register_error_handlers

from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch').setLevel(logging.ERROR)
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('botocore').setLevel(logging.ERROR)
logging.getLogger('s3transfer').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)


app = Flask(__name__)
register_error_handlers(app)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

FaceidView = FaceidView()

@app.route("/face_encoding_create/", methods=["POST"])
def face_encoding_create():
    json = load_json(request.json)
    return FaceidView.face_encoding_create(json)


@app.route("/face_encoding_delete/", methods=["POST"])
def face_encoding_delete():
    json = load_json(request.json)
    return FaceidView.face_encoding_delete(json)


@app.route("/search_faceid/", methods=["POST"])
def search_faceid():
    json = load_json(request.json)
    return FaceidView.search_faceid(json)

@app.route("/search_faceid/unic_identification", methods=["POST"])
def search_faceid_unic():
    json = load_json(request.json)
    return FaceidView.faceid_unic_authentication(json)


@app.route('/version', methods=['GET'])
def version():
    return jsonify(version=1.0)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5500)