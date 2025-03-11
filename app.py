from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from bot_simple import WhatsAppBot
from pdf_knowledge import process_manual
import os
import json
from datetime import datetime
import csv
from io import StringIO

app = Flask(__name__)
bot = WhatsAppBot()

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    stats = bot.obtener_estadisticas()
    
    # Get recent conversations (last 5)
    recent_conversations = []
    if "conversaciones" in stats:
        recent_conversations = sorted(
            stats["conversaciones"], 
            key=lambda x: x.get("fecha", ""), 
            reverse=True
        )[:5]
    
    return render_template('dashboard.html', stats=stats, recent_conversations=recent_conversations)

@app.route('/knowledge')
def knowledge():
    # Check if knowledge base exists
    knowledge_path = os.path.join("logs", "knowledge_base.json")
    knowledge_exists = os.path.exists(knowledge_path)
    
    # Get knowledge base stats if it exists
    knowledge_stats = {}
    if knowledge_exists:
        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
                
            # Count entries by system
            system_counts = {}
            total_entries = 0
            
            for system, problems in knowledge_base.items():
                system_counts[system] = len(problems)
                total_entries += len(problems)
            
            knowledge_stats = {
                "total_entries": total_entries,
                "system_counts": system_counts,
                "last_updated": datetime.fromtimestamp(os.path.getmtime(knowledge_path)).strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            knowledge_stats = {"error": str(e)}
    
    return render_template('knowledge.html', knowledge_exists=knowledge_exists, knowledge_stats=knowledge_stats)

@app.route('/api/message', methods=['POST'])
def receive_message():
    data = request.json
    message = data.get('message', '')
    user_id = data.get('user_id', 'web_user')
    
    response = bot.procesar_mensaje(message, user_id)
    return jsonify({'response': response})

@app.route('/get_stats', methods=['GET'])
def get_stats():
    stats = bot.obtener_estadisticas()
    return jsonify(stats)

@app.route('/estadisticas')
def estadisticas():
    stats = bot.obtener_estadisticas()
    return render_template('estadisticas.html', stats=stats)

@app.route('/stats')
def stats():
    # Obtener parámetros de fecha
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # Obtener estadísticas filtradas por fecha
    stats = bot.obtener_estadisticas(start_date=start_date, end_date=end_date)
    
    return render_template('stats.html', stats=stats)

@app.route('/cargar_manual', methods=['GET', 'POST'])
def cargar_manual():
    if request.method == 'POST':
        if 'manual_pdf' not in request.files:
            return redirect(request.url)
        
        file = request.files['manual_pdf']
        if file.filename == '':
            return redirect(request.url)
        
        if file and file.filename.endswith('.pdf'):
            # Guardar el archivo
            pdf_path = os.path.join('logs', 'manual.pdf')
            file.save(pdf_path)
            
            # Procesar el PDF
            knowledge = process_manual(pdf_path)
            
            # Actualizar el bot con la nueva base de conocimiento
            bot.manual_knowledge = knowledge
            
            return redirect(url_for('knowledge'))
    
    return render_template('cargar_manual.html')

@app.route('/view_conversation/<conversation_id>')
def view_conversation(conversation_id):
    # Load the specific conversation
    conv_path = os.path.join("logs", f"conv_{conversation_id}.json")
    
    if os.path.exists(conv_path):
        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
            return render_template('conversation_detail.html', conversation=conversation)
        except Exception as e:
            return f"Error loading conversation: {e}", 500
    else:
        return "Conversation not found", 404

@app.route('/export_csv', methods=['GET'])
def export_csv():
    # Get stats
    stats = bot.obtener_estadisticas()
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write headers and data
    writer.writerow(['Estadísticas del Bot de Mantenimiento MOC'])
    writer.writerow(['Generado el', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    writer.writerow(['Métricas Generales'])
    writer.writerow(['Total Conversaciones', stats['total_conversaciones']])
    writer.writerow(['Total Mensajes', stats['total_mensajes']])
    writer.writerow(['Tiempo Respuesta Promedio', stats['tiempo_respuesta_promedio']])
    writer.writerow(['Consultas Urgentes', stats['consultas_urgentes']])
    writer.writerow(['Derivaciones a Agente', stats['derivaciones_agente']])
    writer.writerow(['Respuestas Automáticas', stats['respuestas_automaticas']])
    writer.writerow([])
    
    writer.writerow(['Consultas por Sistema'])
    for system, count in stats['consultas_por_sistema'].items():
        writer.writerow([system, count])
    writer.writerow([])
    
    writer.writerow(['Consultas por Problema'])
    for problem, count in stats['consultas_por_problema'].items():
        writer.writerow([problem, count])
    
    # Create response
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=dashboard_stats_{datetime.now().strftime('%Y-%m-%d')}.csv"}
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 