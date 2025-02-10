from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/customer', methods=['POST', 'GET'])
def main():
  payload = request.get_json()
  print(payload)
  return payload

@app.route('/', methods=['GET'])
def home():
  return "Hello, World!"

if __name__ == '__main__':
  app.run(debug=True, port=7203)