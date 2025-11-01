from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({"status": "fakenodo_running"})

# NUEVO ENDPOINT
@app.route('/api/deposit/depositions', methods=['POST'])
def create_record():
    # Simula una respuesta exitosa de Zenodo
    response_data = {
        "id": 12345,
        "conceptrecid": "12344",
        "state": "unsubmitted",
        "metadata": {
            "prereserve_doi": {"doi": "10.5281/zenodo.12345"}
        },
        "links": {
            "publish": "http://localhost:5001/api/deposit/depositions/12345/actions/publish"
        }
    }
    return jsonify(response_data), 201