# api/server.py (Versão com Captura de Erro Detalhada)

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuração ---
GUMROAD_ACCESS_TOKEN = os.environ.get('GUMROAD_ACCESS_TOKEN')
GUMROAD_API_URL = "https://api.gumroad.com/v2/licenses/verify"

@app.route('/', methods=['POST'])
def validate_license():
    if not GUMROAD_ACCESS_TOKEN:
        print("ERROR: Variável de ambiente GUMROAD_ACCESS_TOKEN não encontrada.")
        return jsonify({"success": False, "message": "Erro de configuração do servidor."}), 500

    license_key = request.form.get('license_key')
    product_permalink = request.form.get('product_permalink')

    if not license_key or not product_permalink:
        print(f"ERROR: Pedido incompleto. Chave: {license_key}, Permalink: {product_permalink}")
        return jsonify({"success": False, "message": "Dados da licença ou do produto não fornecidos."}), 400
        
    payload = {
        'access_token': GUMROAD_ACCESS_TOKEN,
        'product_permalink': product_permalink,
        'license_key': license_key.strip()
    }
    
    # =========================================================
    #   BLOCO DE REQUISIÇÃO E CAPTURA DE ERRO DETALHADA
    # =========================================================
    try:
        print(f"INFO: Enviando requisição para a API do Gumroad com permalink '{product_permalink}'.")
        response = requests.post(GUMROAD_API_URL, data=payload, timeout=15)
        
        # Lança um erro para respostas 4xx (erro do cliente) ou 5xx (erro do servidor Gumroad)
        response.raise_for_status() 
        
        data = response.json()
        print(f"INFO: Resposta recebida do Gumroad: {data}")
        
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

    except requests.exceptions.Timeout:
        # Erro específico de timeout (demorou mais de 15 segundos)
        error_message = "A requisição para o servidor do Gumroad demorou muito (timeout)."
        print(f"ERROR: {error_message}") 
        return jsonify({"success": False, "message": error_message}), 504 # Gateway Timeout
        
    except requests.exceptions.RequestException as e:
        # Captura todos os outros erros da biblioteca requests (DNS, SSL, conexão, etc.)
        error_message = "Falha na comunicação com o serviço de licenciamento externo."
        # A mensagem de erro detalhada de 'e' aparecerá nos logs da Vercel
        print(f"CRITICAL_ERROR: {error_message} - Detalhes: {e}") 
        return jsonify({"success": False, "message": error_message}), 503 # Service Unavailable
