from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "sistema": "SISTEMA NUTRI",
        "estado": "En línea",
        "autor": "Armando Imanol Aguilar Espiricueto"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)