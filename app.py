from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os
import json
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type"],
        "supports_credentials": True
    }
})

# Configurações
DATABASE = os.path.join(app.instance_path, 'pedidos.db')
os.makedirs(app.instance_path, exist_ok=True)

# Autenticação para a cozinha
users = {
    "cozinha": generate_password_hash("senhaForte123")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mesa_id INTEGER,
                items TEXT NOT NULL,
                nome_cliente TEXT NOT NULL,
                telefone TEXT,
                endereco TEXT,
                complemento TEXT,
                observacoes TEXT,
                forma_pagamento TEXT NOT NULL,
                troco_para REAL,
                status TEXT DEFAULT 'pendente',
                retirada BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response        

def limpar_pedidos_antigos():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM pedidos 
            WHERE timestamp < datetime('now', '-1 day')
        ''')
        conn.commit()

init_db()
limpar_pedidos_antigos()

# Rotas Públicas
@app.route('/')
def index():
    return redirect(url_for('cardapio', mesa_id=1))

@app.route('/mesa/<int:mesa_id>')
def cardapio(mesa_id=None):
    return render_template('cardapio.html', mesa_id=mesa_id)

# Rotas Protegidas
@app.route('/cozinha')
@auth.login_required
def painel_cozinha():
    return render_template('cozinha.html')

# API Endpoints
@app.route('/fazer_pedido', methods=['POST'])
def fazer_pedido():
    try:
        data = request.get_json()
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pedidos (
                    mesa_id, items, nome_cliente, telefone, endereco,
                    complemento, observacoes, forma_pagamento, troco_para, retirada
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('mesa_id'),
                json.dumps(data['items']),
                data['nome_cliente'],
                data.get('telefone'),
                data.get('endereco'),
                data.get('complemento'),
                data.get('observacoes'),
                data['forma_pagamento'],
                data.get('troco_para'),
                data.get('retirada', False)
            ))
            conn.commit()
            return jsonify({
                "status": "success",
                "pedido_id": cursor.lastrowid
            }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/pedidos')
@auth.login_required
def listar_pedidos():
    try:
        status = request.args.get('status', 'all')
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status == 'all':
                cursor.execute('SELECT * FROM pedidos ORDER BY timestamp DESC')
            else:
                cursor.execute('SELECT * FROM pedidos WHERE status = ? ORDER BY timestamp DESC', (status,))
                
            pedidos = [dict(pedido) for pedido in cursor.fetchall()]
            
            for pedido in pedidos:
                if isinstance(pedido['items'], str):
                    pedido['items'] = json.loads(pedido['items'])
            
            return jsonify(pedidos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/atualizar_status/<int:pedido_id>', methods=['POST'])
@auth.login_required
def atualizar_status(pedido_id):
    try:
        novo_status = request.json.get('status')
        if novo_status not in ['pendente', 'preparando', 'pronto']:
            return jsonify({"error": "Status inválido"}), 400
            
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE pedidos SET status = ? WHERE id = ?', (novo_status, pedido_id))
            conn.commit()
            
            return jsonify({
                "status": "success",
                "message": f"Status atualizado para {novo_status}"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/excluir_pedido/<int:pedido_id>', methods=['DELETE'])
@auth.login_required
def excluir_pedido(pedido_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM pedidos WHERE id = ?', (pedido_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"status": "error", "message": "Pedido não encontrado"}), 404
                
            return jsonify({"status": "success", "message": "Pedido excluído"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)