# api/server.py (Versão FINAL CORRIGIDA usando product_id)

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GUMROAD_ACCESS_TOKEN = os.environ.get('GUMROAD_ACCESS_TOKEN')
GUMROAD_API_URL = "https://api.gumroad.com/v2/licenses/verify"

@app.route('/', methods=['POST'])
def validate_license():
    if not GUMROAD_ACCESS_TOKEN:
        return jsonify({"success": False, "message": "Erro de configuração do servidor."}), 500

    # MUDANÇA: Agora pegamos o product_id em vez do product_permalink
    license_key = request.form.get('license_key')
    product_id = request.form.get('product_id') 

    if not license_key or not product_id:
        return jsonify({"success": False, "message": "Dados da licença ou ID do produto não fornecidos."}), 400
        
    # MUDANÇA: O payload agora usa product_id
    payload = {
        'access_token': GUMROAD_ACCESS_TOKEN,
        'product_id': product_id,
        'license_key': license_key.strip()
    }
    
    try:
        response = requests.post(GUMROAD_API_URL, data=payload, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            uses = data.get("purchase", {}).get("uses", 0)
            MAX_ACTIVATIONS = 3
            
            if uses <= MAX_ACTIVATIONS:
                return jsonify({
                    "valid": True,
                    "message": f"Licença válida. Ativação {uses} de {MAX_ACTIVATIONS}.",
                    "meta": {"status": "active"}
                })
            else:
                return jsonify({
                    "valid": False,
                    "error": "Esta chave de licença atingiu o número máximo de ativações."
                })
        else:
            return jsonify({
                "valid": False,
                "error": data.get("message", "Chave de licença inválida.")
            })

    except requests.RequestException as e:
        return jsonify({"success": False, "message": f"Não foi possível conectar ao serviço de licenciamento: {e}"}), 503
