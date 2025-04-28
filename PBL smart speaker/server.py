from flask import Flask, request, jsonify

app = Flask(__name__)

mood_data = {}

@app.route('/mood', methods=['POST'])
def receive_mood():
    data = request.json
    mood_data['title'] = data.get('title')
    mood_data['artist'] = data.get('artist')
    mood_data['mood'] = data.get('mood')
    print(f"Data diterima: {mood_data}")
    return jsonify({"message": "Data diterima"}), 200

@app.route('/mood', methods=['GET'])
def get_mood():
    return jsonify(mood_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
