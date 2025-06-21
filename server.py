import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# A CHAVE SECRETA DO LEMON SQUEEZY.
# Ela será lida de uma variável de ambiente no servidor, NÃO fica no código.
LEMON_SQUEEZY_API_KEY = os.environ.get('LEMON_SQUEEZY_API_KEY')

# O endpoint oficial do Lemon Squeezy
LEMON_SQUEEZY_VALIDATE_URL = "https://api.lemonsqueezy.com/v1/licenses/validate"

@app.route('/validate', methods=['POST'])
def validate_license():
    # Verifica se a chave de API foi configurada no servidor
    if not LEMON_SQUEEZY_API_KEY:
        return jsonify({"error": "Configuração do servidor incompleta."}), 500

    # Pega os dados enviados pelo seu aplicativo desktop
    license_key = request.form.get('license_key')
    instance_id = request.form.get('instance_id')

    if not license_key:
        return jsonify({"error": "Chave de licença não fornecida."}), 400

    # Prepara a chamada para a API do Lemon Squeezy
    payload = {
        'license_key': license_key,
        'instance_id': instance_id
    }
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {LEMON_SQUEEZY_API_KEY}' # Autenticação!
    }

    try:
        # Repassa a chamada
        response = requests.post(LEMON_SQUEEZY_VALIDATE_URL, data=payload, headers=headers)
        response.raise_for_status() # Lança erro se a resposta for 4xx/5xx

        # Retorna a resposta exata do Lemon Squeezy para o seu app desktop
        return jsonify(response.json())

    except requests.RequestException as e:
        return jsonify({"error": f"Erro de comunicação com o serviço de licença: {e}"}), 503

if __name__ == '__main__':
    # Esta parte é só para testes locais, não será usada na produção
    app.run(debug=True, port=5001)