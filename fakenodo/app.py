from flask import Flask, jsonify, request

app = Flask(__name__)

db = {}
next_id = 1
next_concept_id = 100

@app.route('/')
def health_check():
    return jsonify({"status": "fakenodo_running"})

@app.route('/api/deposit/depositions', methods=['POST'])
def create_record():
    global next_id, next_concept_id
    
    new_id = next_id
    new_concept_id_str = str(next_concept_id)
    
    new_record = {
        "id": new_id,
        "conceptrecid": new_concept_id_str,
        "files_changed": False,
        "state": "unsubmitted",
        "metadata": {
            "prereserve_doi": {"doi": f"10.5281/zenodo.{new_id}"}
        },
        "links": {
            "publish": f"http://localhost:5001/api/deposit/depositions/{new_id}/actions/publish"
        }
    }
    
    db[new_id] = new_record
    
    next_id += 1
    next_concept_id += 1 
    
    return jsonify(new_record), 201

@app.route('/api/deposit/depositions/<int:deposit_id>/files', methods=['POST'])
def simulate_file_change(deposit_id):
    record = db.get(deposit_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    record["files_changed"] = True
    return jsonify({"message": "File change simulated"}), 200


@app.route('/api/deposit/depositions/<int:deposit_id>/actions/publish', methods=['POST'])
def publish_record(deposit_id):
    
    record = db.get(deposit_id)
    
    if not record:
        return jsonify({"error": "Record not found"}), 404

    record["state"] = "published"
    
    if record["files_changed"]:
        record["doi"] = f"10.5281/zenodo.{record['id']}"
    else:
        existing_doi = None
        for r in db.values():
            if r.get('conceptrecid') == record['conceptrecid'] and r.get('state') == 'published' and r.get('doi'):
                existing_doi = r['doi']
                break

        if existing_doi:
            record["doi"] = existing_doi 
        else:
            record["doi"] = f"10.5281/zenodo.{record['id']}"

    return jsonify(record), 202

@app.route('/api/deposit/depositions', methods=['GET'])
def list_versions():
    query_param = request.args.get('q')
    
    if not query_param or 'conceptrecid:' not in query_param:
        return jsonify({"error": "Missing or invalid query param"}), 400
        
    try:
        concept_id = query_param.split(':')[1]
    except IndexError:
        return jsonify({"error": "Invalid query format"}), 400
    
    versions = []
    for record in db.values():
        if record.get('conceptrecid') == concept_id:
            versions.append(record)
            
    return jsonify(versions)
