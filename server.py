# api/server.py (Versão para Gumroad)

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# O SEU TOKEN DE ACESSO SECRETO DO GUMROAD.
# Ele será lido de uma variável de ambiente no servidor.
GUMROAD_ACCESS_TOKEN = os.environ.get('GUMROAD_ACCESS_TOKEN')

# O endpoint da API do Gumroad para verificação de licenças
GUMROAD_API_URL = "https://api.gumroad.com/v2/licenses/verify"

@app.route('/', methods=['POST'])
def validate_license():
    if not GUMROAD_ACCESS_TOKEN:
        return jsonify({"success": False, "message": "Server configuration error."}), 500

    license_key = request.form.get('license_key')
    
    # A API do Gumroad não usa um 'instance_id' como o Lemon Squeezy,
    # mas ela retorna o número de vezes que a chave foi usada.
    # Nós vamos gerenciar o limite de ativações na nossa lógica.
    
    if not license_key:
        return jsonify({"success": False, "message": "License key not provided."}), 400

    # O Gumroad espera um payload com 'product_permalink' e 'license_key'.
    # O 'product_permalink' é o ID do seu produto, que você encontra na URL do produto.
    # Ex: se a URL for gumroad.com/l/meuproduto, o permalink é 'meuproduto'.
    # Vamos passar isso pelo app desktop para mais flexibilidade.
    product_permalink = request.form.get('product_permalink')

    if not product_permalink:
        return jsonify({"success": False, "message": "Product permalink not provided."}), 400
        
    payload = {
        'access_token': GUMROAD_ACCESS_TOKEN, # O Gumroad espera o token no payload
        'product_permalink': product_permalink,
        'license_key': license_key.strip()
    }
    
    try:
        response = requests.post(GUMROAD_API_URL, data=payload, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # A resposta do Gumroad é diferente, então nós a "traduzimos"
        # para um formato consistente para o nosso app.
        if data.get("success"):
            # A chave é válida, agora verificamos se ainda pode ser usada.
            uses = data.get("purchase", {}).get("uses", 0)
            
            # Defina seu próprio limite de ativações aqui! Ex: 3 ativações.
            MAX_ACTIVATIONS = 3
            
            if uses < MAX_ACTIVATIONS:
                # Retornamos um formato parecido com o do Lemon Squeezy para o nosso app
                return jsonify({
                    "valid": True,
                    "message": f"License is valid. Activation {uses + 1} of {MAX_ACTIVATIONS}.",
                    "meta": {"uses": uses}
                })
            else:
                return jsonify({
                    "valid": False,
                    "error": "This license key has reached its maximum number of activations."
                })
        else:
            # A chave é inválida ou o produto não corresponde.
            return jsonify({
                "valid": False,
                "error": data.get("message", "Invalid license key.")
            })

    except requests.RequestException as e:
        return jsonify({"success": False, "message": f"Could not connect to the licensing service: {e}"}), 503
