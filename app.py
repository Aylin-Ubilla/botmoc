from flask import Flask, render_template, request, jsonify
from bot_simple import WhatsAppBot
import os

app = Flask(__name__)
bot = WhatsAppBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/message', methods=['POST'])
def receive_message():
    data = request.json
    message = data.get('message', '')
    user_id = data.get('user_id', 'web_user')
    
    response = bot.procesar_mensaje(message, user_id)
    return jsonify({'response': response})

# Punto de entrada para Render
if __name__ == '__main__':
    # Obtener el puerto de la variable de entorno o usar 10000 como predeterminado
    port = int(os.environ.get('PORT', 10000))
    # Ejecutar la aplicación en modo producción
    app.run(host='0.0.0.0', port=port, debug=False)