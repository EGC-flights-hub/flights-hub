from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({"status": "fakenodo_running"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)