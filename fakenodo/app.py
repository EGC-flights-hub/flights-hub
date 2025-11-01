from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({"status": "fakenodo_running"})

@app.route('/api/deposit/depositions', methods=['POST'])
def create_record():
    response_data = {
        "id": 12345,
        "conceptrecid": "12344",
        "state": "unsubmitted",
        "metadata": {
            "prereserve_doi": {"doi": "10.5281/zenodo.12345"}
        },
        "links": {
            "publish": "http://localhost:5000/api/deposit/depositions/12345/actions/publish"
        }
    }
    return jsonify(response_data), 201


@app.route('/api/deposit/depositions/<int:deposit_id>/actions/publish', methods=['POST'])
def publish_record(deposit_id):
    # Simula una respuesta de publicación exitosa
    response_data = {
        "id": deposit_id,
        "state": "published",
        "doi": "10.5281/zenodo.12345"
        
    }
    return jsonify(response_data), 202