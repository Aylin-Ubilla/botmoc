import os
import re
import json
from datetime import datetime
from collections import defaultdict
import random
import time
import uuid
from pdf_knowledge import ManualKnowledge

class WhatsAppBot:
    def __init__(self):
        # Sistemas y problemas con palabras clave expandidas
        self.sistemas = {
            'APU': ['apu', 'auxiliary', 'auxiliar', 'power unit', 'unidad auxiliar'],
            'MOTOR': ['motor', 'engine', 'engines', 'powerplant', 'motores', 'turbina', 'propulsor', 'n1', 'n2'],
            'TREN': ['tren', 'gear', 'landing', 'lgear', 'ruedas', 'aterrizaje', 'mlg', 'nlg', 'llantas'],
            'HIDRAULICO': ['hidraulico', 'hydraulic', 'hyd', 'presion', 'fluido', 'fluid', 'presión', 'bomba', 'pump'],
            'ELECTRICO': ['electrico', 'electrical', 'power', 'bateria', 'energia', 'battery', 'electric', 'luz', 'light'],
            'CABINA': ['cabina', 'cabin', 'pax', 'pasajeros', 'passenger', 'asientos', 'seats', 'oxigeno', 'oxygen'],
            'GALLEY': ['galley', 'cocina', 'catering', 'comida', 'food', 'bebida', 'drink', 'horno', 'oven']
        }
        
        # Problemas con frases completas
        self.problemas = {
            'NO_ARRANCA': ['no arranca', 'no enciende', 'no prende', 'falla arranque', 'problema arranque', 
                          'won\'t start', 'no start', 'failed to start', 'start failure'],
            'NO_FUNCIONA': ['no funciona', 'no opera', 'inoperativo', 'falla', 'mal funcionamiento', 
                           'not working', 'inoperative', 'failure', 'malfunction', 'broken'],
            'ERROR': ['error', 'warning', 'alerta', 'mensaje', 'indicacion', 'luz', 'indication', 
                     'light', 'caution', 'fault', 'code', 'código'],
            'REVISAR': ['revisar', 'verificar', 'chequear', 'check', 'inspeccionar', 'inspect', 
                       'review', 'examine', 'test', 'probar']
        }
        
        # Historial de conversaciones
        self.conversaciones = defaultdict(list)
        self.contexto_actual = {}
        
        # Cargar respuestas predefinidas
        self.respuestas_comunes = {
            'saludo': ['Hola', 'Buen día', 'Saludos', 'Hola, ¿en qué puedo ayudarte?'],
            'despedida': ['Hasta luego', 'Adiós', 'Que tengas buen día', 'Gracias por contactarnos'],
            'agradecimiento': ['De nada', 'Con gusto', 'Para servirte', 'Estamos para ayudar']
        }
        
        # Respuestas automatizadas para casos comunes
        self.respuestas_automaticas = {
            ('APU', 'NO_ARRANCA'): [
                "Para problemas de arranque de APU, verifica lo siguiente:\n\n"
                "1. Asegúrate que el interruptor de batería esté en posición ON\n"
                "2. Verifica que el nivel de combustible sea adecuado\n"
                "3. Comprueba que no haya mensajes de error en el ECAM/EICAS\n"
                "4. Intenta un ciclo completo de apagado y encendido\n\n"
                "Si el problema persiste, proporciona más detalles para ayudarte mejor."
            ],
            ('MOTOR', 'NO_ARRANCA'): [
                "Para problemas de arranque de motor, verifica lo siguiente:\n\n"
                "1. Asegúrate que el suministro de combustible sea adecuado\n"
                "2. Verifica que el sistema de ignición esté funcionando correctamente\n"
                "3. Comprueba que no haya mensajes de error en el ECAM/EICAS\n"
                "4. Revisa el procedimiento de arranque en el manual\n\n"
                "Si el problema persiste, proporciona más detalles para ayudarte mejor."
            ],
            ('TREN', 'NO_FUNCIONA'): [
                "Para problemas con el tren de aterrizaje, verifica lo siguiente:\n\n"
                "1. Comprueba el sistema hidráulico y nivel de presión\n"
                "2. Verifica que no haya obstrucciones mecánicas\n"
                "3. Revisa los indicadores de posición del tren\n"
                "4. Considera usar el sistema de extensión de emergencia si es necesario\n\n"
                "Si el problema persiste, proporciona más detalles para ayudarte mejor."
            ],
            ('HIDRAULICO', 'ERROR'): [
                "Para problemas con el sistema hidráulico, verifica lo siguiente:\n\n"
                "1. Comprueba el nivel de fluido hidráulico\n"
                "2. Verifica que no haya fugas visibles\n"
                "3. Revisa la presión del sistema\n"
                "4. Comprueba el funcionamiento de las bombas\n\n"
                "Si el problema persiste, proporciona más detalles para ayudarte mejor."
            ],
            ('ELECTRICO', 'ERROR'): [
                "Para problemas con el sistema eléctrico, verifica lo siguiente:\n\n"
                "1. Comprueba los disyuntores (circuit breakers)\n"
                "2. Verifica el estado de las baterías\n"
                "3. Revisa las conexiones de los generadores\n"
                "4. Comprueba los buses eléctricos principales\n\n"
                "Si el problema persiste, proporciona más detalles para ayudarte mejor."
            ],
            ('GALLEY', 'NO_FUNCIONA'): [
                "Para problemas con el galley, verifica lo siguiente:\n\n"
                "1. Comprueba que el interruptor de alimentación esté activado\n"
                "2. Verifica que el sistema eléctrico del galley esté operativo\n"
                "3. Revisa los disyuntores específicos del galley\n"
                "4. Comprueba las conexiones de los equipos\n\n"
                "Si el problema persiste, proporciona más detalles para ayudarte mejor."
            ]
        }
        
        # Respuestas para problemas específicos
        self.respuestas_especificas = {
            'apu overheat': "Para un mensaje de APU OVERHEAT:\n\n"
                           "1. Apaga el APU inmediatamente\n"
                           "2. Verifica posibles fugas de fluidos alrededor del APU\n"
                           "3. Espera al menos 30 minutos para enfriamiento\n"
                           "4. Consulta el MEL para determinar si el vuelo puede continuar\n\n"
                           "Este problema requiere inspección de mantenimiento antes del próximo vuelo.",
            
            'low oil pressure': "Para un mensaje de LOW OIL PRESSURE:\n\n"
                               "1. Monitorea la presión de aceite y temperatura\n"
                               "2. Reduce la potencia del motor si es posible\n"
                               "3. Prepárate para un posible apagado del motor\n"
                               "4. Consulta el QRH para el procedimiento específico\n\n"
                               "Este problema requiere atención inmediata de mantenimiento.",
            
            'hydraulic low level': "Para un mensaje de HYDRAULIC LOW LEVEL:\n\n"
                                  "1. Verifica posibles fugas en el sistema hidráulico\n"
                                  "2. Monitorea la presión del sistema\n"
                                  "3. Considera las limitaciones de operación\n"
                                  "4. Consulta el MEL para determinar restricciones\n\n"
                                  "Este problema requiere inspección de mantenimiento antes del próximo vuelo.",
            
            'cargo door': "Para problemas con la puerta de carga:\n\n"
                         "1. Verifica que los mecanismos de cierre estén correctamente enganchados\n"
                         "2. Comprueba que no haya obstrucciones en los sellos\n"
                         "3. Revisa los indicadores de estado de la puerta\n"
                         "4. Considera un reinicio del sistema eléctrico\n\n"
                         "Si el problema persiste, se requiere inspección de mantenimiento."
        }

        # Añadir configuración para el registro de conversaciones
        self.log_dir = "logs"
        self.stats_file = "conversation_stats.json"
        
        # Crear directorio de logs si no existe
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Inicializar estadísticas
        self.stats = self.cargar_estadisticas()
        
        # Cargar base de conocimiento del manual
        self.manual_knowledge = ManualKnowledge()
        knowledge_path = os.path.join(self.log_dir, 'knowledge_base.json')
        if os.path.exists(knowledge_path):
            self.manual_knowledge.load_knowledge_base(knowledge_path)
        else:
            print("No se encontró la base de conocimiento del manual.")

    def cargar_estadisticas(self):
        """Carga las estadísticas desde el archivo JSON"""
        stats_path = os.path.join(self.log_dir, self.stats_file)
        if os.path.exists(stats_path):
            try:
                with open(stats_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error al cargar estadísticas: {e}")
                return self.inicializar_estadisticas()
        else:
            return self.inicializar_estadisticas()
    
    def inicializar_estadisticas(self):
        """Inicializa la estructura de estadísticas"""
        return {
            "total_conversaciones": 0,
            "total_mensajes": 0,
            "tiempo_respuesta_promedio": 0,
            "consultas_por_sistema": {},
            "consultas_por_problema": {},
            "consultas_urgentes": 0,
            "derivaciones_agente": 0,
            "respuestas_automaticas": 0,
            "conversaciones": [],
            "consultas_satisfactorias": 0,
            "total_encuestas": 0
        }
    
    def guardar_estadisticas(self):
        """Guarda las estadísticas en el archivo JSON"""
        stats_path = os.path.join(self.log_dir, self.stats_file)
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar estadísticas: {e}")
    
    def registrar_conversacion(self, id_usuario, mensajes, sistema=None, problema=None, matricula=None, es_urgente=False, derivado_agente=False, respuesta_automatica=False):
        """Registra una conversación completa en las estadísticas"""
        # Incrementar contadores
        self.stats["total_conversaciones"] += 1
        self.stats["total_mensajes"] += len(mensajes)
        
        if es_urgente:
            self.stats["consultas_urgentes"] += 1
        
        if derivado_agente:
            self.stats["derivaciones_agente"] += 1
        
        if respuesta_automatica:
            self.stats["respuestas_automaticas"] += 1
        
        # Registrar sistema y problema
        if sistema:
            self.stats["consultas_por_sistema"][sistema] = self.stats["consultas_por_sistema"].get(sistema, 0) + 1
        
        if problema:
            self.stats["consultas_por_problema"][problema] = self.stats["consultas_por_problema"].get(problema, 0) + 1
        
        # Crear registro de conversación
        conversacion = {
            "id": str(uuid.uuid4()),
            "id_usuario": id_usuario,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sistema": sistema,
            "problema": problema,
            "matricula": matricula,
            "es_urgente": es_urgente,
            "derivado_agente": derivado_agente,
            "respuesta_automatica": respuesta_automatica,
            "mensajes": mensajes
        }
        
        # Añadir a la lista de conversaciones
        self.stats["conversaciones"].append(conversacion)
        
        # Guardar estadísticas actualizadas
        self.guardar_estadisticas()
        
        # También guardar esta conversación en un archivo separado para facilitar la búsqueda
        self.guardar_conversacion_individual(conversacion)
    
    def guardar_conversacion_individual(self, conversacion):
        """Guarda una conversación individual en un archivo JSON separado"""
        conv_id = conversacion["id"]
        conv_path = os.path.join(self.log_dir, f"conv_{conv_id}.json")
        try:
            with open(conv_path, 'w', encoding='utf-8') as f:
                json.dump(conversacion, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar conversación individual: {e}")

    def detectar_sistema_y_problema(self, mensaje):
        """Detecta el sistema, problema y matrícula mencionados en el mensaje"""
        mensaje_lower = mensaje.lower()
        
        # Sistemas posibles (ampliados y mejorados)
        sistemas = {
            'apu': ['apu', 'auxiliary power unit', 'unidad auxiliar'],
            'motor': ['motor', 'engine', 'turbina', 'propulsor'],
            'tren': ['tren', 'landing gear', 'ruedas', 'aterrizaje', 'landing'],
            'hidraulico': ['hidraulico', 'hydraulic', 'hidráulico', 'fluido'],
            'electrico': ['electrico', 'eléctrico', 'electric', 'electrical', 'sistema eléctrico'],
            'cabina': ['cabina', 'cockpit', 'panel', 'instrumentos'],
            'galley': ['galley', 'cocina', 'catering']
        }
        
        # Problemas posibles (ampliados y mejorados)
        problemas = {
            'NO_ARRANCA': ['no arranca', 'no enciende', 'no prende', 'won\'t start', 'no start'],
            'NO_FUNCIONA': ['no funciona', 'no opera', 'inoperativo', 'falla', 'not working', 'doesn\'t work', 'fallo'],
            'ERROR': ['error', 'warning', 'alerta', 'mensaje', 'indicador', 'luz'],
            'REVISAR': ['revisar', 'verificar', 'check', 'inspeccionar', 'comprobar', 'verificación'],
            'RESET': ['reset', 'reinicio', 'reiniciar', 'resetear', 'restart']
        }
        
        # Detectar sistema con mayor flexibilidad
        sistema_detectado = None
        for sistema, keywords in sistemas.items():
            for keyword in keywords:
                if keyword in mensaje_lower:
                    sistema_detectado = sistema.upper()
                    break
            if sistema_detectado:
                break
        
        # Detectar problema con mayor flexibilidad
        problema_detectado = None
        for problema, keywords in problemas.items():
            for keyword in keywords:
                if keyword in mensaje_lower:
                    problema_detectado = problema
                    break
            if problema_detectado:
                break
        
        # Caso especial para "check" o "verificar" + sistema
        if 'check' in mensaje_lower or 'verificar' in mensaje_lower or 'revisar' in mensaje_lower:
            problema_detectado = 'REVISAR'
        
        # Si no se detectó un problema específico pero hay palabras como "problema" o "issue"
        if not problema_detectado and ('problema' in mensaje_lower or 'issue' in mensaje_lower or 'falla' in mensaje_lower):
            problema_detectado = 'NO_FUNCIONA'  # Asignar un problema genérico
        
        # Detectar matrícula (formato CC-XXX) con mayor flexibilidad
        matricula_match = re.search(r'CC-[A-Z]{3}', mensaje.upper())
        if not matricula_match:
            # Intentar otros formatos como "CC XXX" o "CCXXX"
            matricula_match = re.search(r'CC\s+[A-Z]{3}', mensaje.upper())
            if matricula_match:
                matricula_detectada = matricula_match.group(0).replace(' ', '-')
            else:
                matricula_match = re.search(r'CC[A-Z]{3}', mensaje.upper())
                if matricula_match:
                    texto = matricula_match.group(0)
                    matricula_detectada = f"{texto[:2]}-{texto[2:]}"
                else:
                    matricula_detectada = None
        else:
            matricula_detectada = matricula_match.group(0)
        
        # Imprimir para depuración
        print(f"Sistema detectado: {sistema_detectado}, Problema detectado: {problema_detectado}, Matrícula detectada: {matricula_detectada}")
        
        return sistema_detectado, problema_detectado, matricula_detectada

    def detectar_problema_especifico(self, texto):
        """Detecta problemas específicos en el texto"""
        texto = texto.lower()
        
        for problema_clave in self.respuestas_especificas.keys():
            if problema_clave in texto:
                return problema_clave
        
        return None

    def obtener_contexto(self, id_usuario):
        """Recupera el contexto de la conversación actual"""
        return self.contexto_actual.get(id_usuario, {})

    def procesar_mensaje(self, mensaje, id_usuario="web_user"):
        # Registrar tiempo de inicio
        tiempo_inicio = time.time()
        
        # Inicializar contexto si no existe
        if id_usuario not in self.contexto_actual:
            self.contexto_actual[id_usuario] = {}
        
        # Verificar si el usuario está en una encuesta de satisfacción
        if 'en_encuesta' in self.contexto_actual[id_usuario] and self.contexto_actual[id_usuario]['en_encuesta']:
            # Procesar respuesta de la encuesta
            respuesta = self.procesar_respuesta_encuesta(mensaje, id_usuario)
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            return respuesta
        
        # Verificar si estamos en proceso de recopilación de información para agente
        if 'recopilando_info_agente' in self.contexto_actual[id_usuario] and self.contexto_actual[id_usuario]['recopilando_info_agente']:
            respuesta = self.procesar_recopilacion_info_agente(mensaje, id_usuario)
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            return respuesta
        
        # Verificar si el mensaje es "agente" después de una encuesta negativa
        if mensaje.lower() == 'agente' and self.contexto_actual[id_usuario].get('encuesta_respondida', False):
            return self.iniciar_recopilacion_info_agente(id_usuario, tiempo_inicio)
        
        # Verificar si el mensaje indica que el usuario no necesita más ayuda
        if self.es_mensaje_despedida(mensaje):
            # Verificar si ya se ha enviado una encuesta anteriormente
            if not self.contexto_actual[id_usuario].get('encuesta_respondida', False):
                # Enviar la encuesta solo si no se ha respondido antes
                self.contexto_actual[id_usuario]['en_encuesta'] = True
                respuesta = "¿El problema o tu consulta fue resuelta? Responde Sí o No."
                self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
                return respuesta
            else:
                # Si ya se respondió, enviar un mensaje de despedida
                respuesta = "Gracias por usar nuestro servicio. ¡Que tengas un buen día!"
                self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
                return respuesta
        
        # Verificar si el mensaje es "agente" o solicita contacto con agente
        if mensaje.lower() == 'agente' or 'contactar' in mensaje.lower() or 'hablar con agente' in mensaje.lower():
            # Iniciar proceso de recopilación de información
            return self.iniciar_recopilacion_info_agente(id_usuario, tiempo_inicio)
        
        # Verificar si es un mensaje repetido
        ultimo_mensaje = None
        penultimo_mensaje = None
        if id_usuario in self.conversaciones and len(self.conversaciones[id_usuario]) >= 1:
            for msg in reversed(self.conversaciones[id_usuario]):
                if msg.get('tipo') == 'usuario':
                    if ultimo_mensaje is None:
                        ultimo_mensaje = msg.get('mensaje', '')
                    elif penultimo_mensaje is None:
                        penultimo_mensaje = msg.get('mensaje', '')
                        break
        
        # Si el mensaje actual es igual al último mensaje del usuario
        if ultimo_mensaje and mensaje.lower() == ultimo_mensaje.lower():
            # Verificar si también es igual al penúltimo mensaje (repetición múltiple)
            if penultimo_mensaje and mensaje.lower() == penultimo_mensaje.lower():
                # Detectar sistema y problema para dar una respuesta más específica
                sistema, problema, matricula = self.detectar_sistema_y_problema(mensaje)
                
                if sistema and problema:
                    # Si podemos detectar sistema y problema, dar una respuesta específica
                    respuesta = f"Veo que estás mencionando un problema con {sistema}. Para ayudarte mejor, necesito más detalles específicos sobre el problema '{problema}'. ¿Podrías proporcionar información adicional como mensajes de error, cuándo comenzó el problema o qué acciones has intentado?"
                else:
                    # Si no podemos detectar sistema y problema, dar una respuesta genérica
                    respuesta = "Parece que estás enviando el mismo mensaje varias veces. Para ayudarte mejor, necesito más detalles sobre tu consulta. ¿Podrías proporcionar más información o explicar tu problema de otra manera?"
                
                self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
                return respuesta
        
        # Guardar mensaje en historial
        self.conversaciones[id_usuario].append({
            'mensaje': mensaje,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'tipo': 'usuario'
        })
        
        # Variables para registro
        es_urgente = False
        derivado_agente = False
        respuesta_automatica = False
        
        # Comandos especiales - verificar primero
        mensaje_lower = mensaje.lower()
        
        # Verificar si el usuario quiere iniciar una nueva consulta
        if mensaje_lower in ['nueva consulta', 'nuevo problema', 'otra consulta', 'reiniciar']:
            self.reiniciar_conversacion(id_usuario)
            respuesta = "Entendido. ¿En qué puedo ayudarte con esta nueva consulta?"
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            return respuesta
        
        # Resto de comandos especiales
        if mensaje_lower == 'ayuda':
            respuesta = self.mostrar_ayuda()
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            return respuesta
        elif mensaje_lower == 'ejemplos':
            respuesta = self.mostrar_ejemplos()
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            return respuesta
        elif mensaje_lower == 'urgente':
            es_urgente = True
            respuesta = "He marcado tu caso como urgente. Un agente de mantenimiento te contactará lo antes posible. Mientras tanto, ¿puedes proporcionar más detalles sobre el problema?"
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio, es_urgente=True)
            return respuesta
        
        # Detectar preguntas sobre reset
        if ('reset' in mensaje_lower or 'reinicio' in mensaje_lower or 'reiniciar' in mensaje_lower or 
            'como hago el reset' in mensaje_lower or 'cómo hago el reset' in mensaje_lower):
            
            # Detectar sistema mencionado en el mensaje
            sistema = None
            if 'apu' in mensaje_lower:
                sistema = 'APU'
            elif 'electrico' in mensaje_lower or 'eléctrico' in mensaje_lower:
                sistema = 'ELECTRICO'
            elif 'tren' in mensaje_lower or 'aterrizaje' in mensaje_lower:
                sistema = 'TREN'
            
            # Si no se detecta sistema en el mensaje, intentar obtenerlo del contexto
            if not sistema:
                contexto = self.obtener_contexto(id_usuario)
                sistema = contexto.get('sistema')
            
            respuesta = self.manejar_reset_sistema(id_usuario, sistema)
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            
            # Determinar si debemos enviar la encuesta
            if not self.contexto_actual[id_usuario].get('encuesta_respondida', False):
                self.contexto_actual[id_usuario]['en_encuesta'] = True
                respuesta += "\n\n¿El problema o tu consulta fue resuelta? Responde Sí o No."
            
            return respuesta
        
        # Detectar sistema, problema y matrícula
        sistema, problema, matricula = self.detectar_sistema_y_problema(mensaje)
        
        # Caso especial para "APU no arranca"
        if (sistema == 'APU' and problema == 'NO_ARRANCA') or ('apu' in mensaje_lower and ('no arranca' in mensaje_lower or 'no enciende' in mensaje_lower)):
            # Obtener contexto actual
            contexto = self.obtener_contexto(id_usuario)
            
            # Actualizar contexto con la información detectada
            contexto['sistema'] = 'APU'
            contexto['problema'] = 'NO_ARRANCA'
            if matricula:
                contexto['matricula'] = matricula
            
            # Guardar contexto actualizado
            self.contexto_actual[id_usuario] = contexto
            
            # Si ya tenemos la matrícula, dar la solución completa
            if matricula or contexto.get('matricula'):
                matricula_final = matricula or contexto.get('matricula')
                
                respuesta = (f"Para solucionar el problema de APU que no arranca en {matricula_final}, verifica lo siguiente:\n\n"
                            f"1. Comprueba que el interruptor de control del APU esté en posición ON\n"
                            f"2. Verifica el nivel de combustible y que la válvula de combustible del APU esté abierta\n"
                            f"3. Revisa los breakers relacionados con el APU en el panel eléctrico\n"
                            f"4. Comprueba si hay mensajes de error específicos en la ECAM/EICAS\n"
                            f"5. Verifica que la temperatura exterior esté dentro de los límites operativos del APU\n\n"
                            f"Si después de estas verificaciones el APU sigue sin arrancar, podría ser necesario realizar un reset del sistema o contactar al equipo de mantenimiento para una inspección más detallada.")
                
                self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
                
                # Determinar si debemos enviar la encuesta
                if not self.contexto_actual[id_usuario].get('encuesta_respondida', False):
                    self.contexto_actual[id_usuario]['en_encuesta'] = True
                    respuesta += "\n\n¿El problema o tu consulta fue resuelta? Responde Sí o No."
                
                return respuesta
            else:
                # Si no tenemos la matrícula, pedirla
                respuesta = "Detecto que el APU no arranca. ¿Podrías indicarme la matrícula de la aeronave?"
                self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
                return respuesta
        
        # Caso especial para "Tren de aterrizaje"
        if (sistema == 'TREN') or ('tren' in mensaje_lower and 'aterrizaje' in mensaje_lower):
            problema_tren = problema or 'REVISAR'  # Si no detectamos problema específico, asumir REVISAR
            respuesta = self.manejar_tren_aterrizaje(id_usuario, problema_tren, matricula)
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            
            # Determinar si debemos enviar la encuesta
            if matricula and not self.contexto_actual[id_usuario].get('encuesta_respondida', False):
                self.contexto_actual[id_usuario]['en_encuesta'] = True
                respuesta += "\n\n¿El problema o tu consulta fue resuelta? Responde Sí o No."
            
            return respuesta
        
        # Caso especial para "Sistema eléctrico"
        if (sistema == 'ELECTRICO') or ('electrico' in mensaje_lower or 'eléctrico' in mensaje_lower):
            problema_elec = problema or 'REVISAR'  # Si no detectamos problema específico, asumir REVISAR
            respuesta = self.manejar_sistema_electrico(id_usuario, problema_elec, matricula)
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            
            # Determinar si debemos enviar la encuesta
            if matricula and not self.contexto_actual[id_usuario].get('encuesta_respondida', False):
                self.contexto_actual[id_usuario]['en_encuesta'] = True
                respuesta += "\n\n¿El problema o tu consulta fue resuelta? Responde Sí o No."
            
            return respuesta
        
        # Manejar mensajes cortos o ambiguos
        if len(mensaje.strip()) <= 5:
            respuesta = self.manejar_mensaje_corto(mensaje, id_usuario)
            self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
            return respuesta
        
        # Detectar si hay un cambio de tema
        if self.detectar_cambio_tema(mensaje, id_usuario):
            # Reiniciar el contexto pero mantener el estado de la encuesta
            encuesta_respondida = self.contexto_actual[id_usuario].get('encuesta_respondida', False)
            self.contexto_actual[id_usuario] = {'encuesta_respondida': encuesta_respondida}
            print(f"Detectado cambio de tema para usuario {id_usuario}")
        
        # Al final, registrar la respuesta y el tiempo
        respuesta = self.procesar_mensaje_normal(mensaje, id_usuario, sistema, problema, matricula)
        self.registrar_respuesta(id_usuario, respuesta, tiempo_inicio)
        
        # Determinar si la conversación ha terminado y debemos enviar la encuesta
        # Condiciones para considerar que una conversación ha terminado:
        # 1. No es una solicitud de agente (porque eso derivaría a un humano)
        # 2. No es una consulta urgente (porque eso requiere seguimiento)
        # 3. No es un comando de ayuda o ejemplos (porque son informativos)
        # 4. La respuesta contiene una solución completa (verificamos por palabras clave)
        # 5. El usuario ha enviado al menos 2 mensajes (para evitar encuestas prematuras)
        
        conversacion_terminada = (
            not derivado_agente and 
            not es_urgente and 
            not mensaje_lower in ['ayuda', 'ejemplos'] and
            len(self.conversaciones.get(id_usuario, [])) >= 2 and
            self._es_respuesta_final(respuesta) and
            not self.contexto_actual[id_usuario].get('encuesta_respondida', False)  # No enviar si ya se respondió
        )
        
        if conversacion_terminada:
            # Añadir la encuesta al final de la respuesta
            self.contexto_actual[id_usuario]['en_encuesta'] = True
            respuesta += "\n\n¿El problema o tu consulta fue resuelta? Responde Sí o No."
        
        return respuesta
    
    def procesar_mensaje_normal(self, mensaje, id_usuario, sistema, problema, matricula):
        """Procesa el mensaje normalmente"""
        # Obtener contexto actual
        contexto = self.obtener_contexto(id_usuario)
        
        # Verificar si ya se respondió a la encuesta anteriormente
        if contexto.get('encuesta_respondida', False) and mensaje.lower() != 'agente':
            # Si ya se respondió a la encuesta y no es una solicitud de agente,
            # iniciar una nueva conversación
            return "¿En qué más puedo ayudarte hoy? Por favor, describe tu consulta."
        
        # Verificar si el mensaje es una pregunta de seguimiento sobre un tema anterior
        mensaje_lower = mensaje.lower()
        ultimo_tema = contexto.get('ultimo_tema', '')
        
        # Preguntas de seguimiento sobre reset
        if ('como' in mensaje_lower or 'cómo' in mensaje_lower) and 'reset' in ultimo_tema:
            sistema = ultimo_tema.replace('reset_', '').upper()
            return self.manejar_reset_sistema(id_usuario, sistema)
        
        # Lista ampliada de frases que indican que el usuario no necesita más ayuda
        frases_despedida = [
            'no', 'no gracias', 'no necesito más ayuda', 'no hay más', 'nada más', 'es todo',
            'nada mas', 'nada mas gracias', 'eso es todo', 'listo', 'terminamos', 'gracias',
            'muchas gracias', 'eso sería todo', 'no hay nada más', 'no hay nada mas',
            'contactar', 'contáctar', 'contactame', 'contáctame'
        ]
        
        # Verificar si el mensaje indica que no necesita más ayuda
        if any(frase in mensaje_lower for frase in frases_despedida):
            # Verificar si ya se ha enviado una encuesta anteriormente
            if not contexto.get('encuesta_respondida', False):
                # Enviar la encuesta solo si no se ha respondido antes
                return "¿El problema o tu consulta fue resuelta? Responde Sí o No."
            else:
                # Si ya se respondió, enviar un mensaje de despedida
                return "Gracias por usar nuestro servicio. ¡Que tengas un buen día!"
        
        # Guardar información detectada en el contexto
        if sistema:
            contexto['sistema'] = sistema
        if problema:
            contexto['problema'] = problema
        if matricula:
            contexto['matricula'] = matricula
        
        # Obtener información del contexto si no se detectó en el mensaje actual
        sistema = sistema or contexto.get('sistema')
        problema = problema or contexto.get('problema')
        matricula = matricula or contexto.get('matricula')
        
        # Actualizar el contexto
        self.contexto_actual[id_usuario] = contexto
        
        # Si detectamos sistema y problema pero no matrícula, pedir matrícula
        if sistema and problema and not matricula:
            return f"Detecto {problema} en {sistema}. ¿Podrías indicarme la matrícula de la aeronave?"
        
        # Si solo detectamos sistema pero no problema, pedir problema
        if sistema and not problema:
            return f"Entiendo que mencionas el sistema {sistema}. ¿Qué problema específico estás experimentando?"
        
        # Si solo detectamos problema pero no sistema, pedir sistema
        if problema and not sistema:
            return f"Entiendo que hay un {problema}. ¿En qué sistema específico de la aeronave?"
        
        # Si tenemos sistema y problema, generar respuesta
        if sistema and problema:
            # Generar una respuesta más completa que incluya palabras clave de solución
            respuesta = self.generar_respuesta_automatica(sistema, problema)
            
            # Añadir un cierre que indique que es una respuesta final
            respuesta += "\n\nSi el problema persiste, proporciona más detalles o escribe 'agente' para hablar con un especialista."
            
            return respuesta
        
        # Si no detectamos ni sistema ni problema, pedir más información
        return ("No pude identificar claramente tu consulta. Para ayudarte mejor, por favor especifica:\n"
                "- El sistema afectado (APU, Motor, Tren, etc.)\n"
                "- El problema (no arranca, no funciona, error, etc.)\n"
                "- La matrícula de la aeronave\n\n"
                "Ejemplo: 'El APU del CC-AWN no arranca'\n"
                "Escribe 'ejemplos' para ver más casos de uso.")
    
    def registrar_respuesta(self, id_usuario, respuesta, tiempo_inicio):
        """Registra la respuesta del bot y el tiempo de respuesta"""
        tiempo_respuesta = time.time() - tiempo_inicio
        
        # Actualizar tiempo promedio de respuesta
        total_mensajes = self.stats["total_mensajes"]
        tiempo_promedio_actual = self.stats["tiempo_respuesta_promedio"]
        
        if total_mensajes > 0:
            nuevo_tiempo_promedio = (tiempo_promedio_actual * total_mensajes + tiempo_respuesta) / (total_mensajes + 1)
            self.stats["tiempo_respuesta_promedio"] = nuevo_tiempo_promedio
        else:
            self.stats["tiempo_respuesta_promedio"] = tiempo_respuesta
        
        # Guardar respuesta en historial
        self.conversaciones[id_usuario].append({
            'mensaje': respuesta,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'tiempo_respuesta': tiempo_respuesta,
            'tipo': 'bot'
        })
    
    # Añadir un método para obtener estadísticas
    def obtener_estadisticas(self, start_date=None, end_date=None):
        """Devuelve un resumen de las estadísticas, opcionalmente filtrado por fechas"""
        # Obtener la fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        # Obtener la fecha del primer registro (o usar None si no hay registros)
        fecha_inicio = None
        if self.stats["conversaciones"] and len(self.stats["conversaciones"]) > 0:
            fecha_inicio = self.stats["conversaciones"][0]["fecha"].split()[0]  # Solo la parte de la fecha
        
        # Si no hay filtros de fecha, devolver todas las estadísticas
        if not start_date and not end_date:
            return {
                "total_conversaciones": self.stats["total_conversaciones"],
                "total_mensajes": self.stats["total_mensajes"],
                "tiempo_respuesta_promedio": round(self.stats["tiempo_respuesta_promedio"], 3),
                "consultas_por_sistema": self.stats["consultas_por_sistema"],
                "consultas_por_problema": self.stats["consultas_por_problema"],
                "consultas_urgentes": self.stats["consultas_urgentes"],
                "derivaciones_agente": self.stats["derivaciones_agente"],
                "respuestas_automaticas": self.stats["respuestas_automaticas"],
                "fecha_actual": fecha_actual,
                "fecha_inicio": fecha_inicio,
                "start_date": start_date,
                "end_date": end_date,
                "consultas_satisfactorias": self.stats["consultas_satisfactorias"],
                "total_encuestas": self.stats["total_encuestas"]
            }
        
        # Para simplificar, si hay filtros de fecha pero no tenemos implementada la lógica completa,
        # devolvemos las estadísticas completas pero incluimos los filtros en la respuesta
        return {
            "total_conversaciones": self.stats["total_conversaciones"],
            "total_mensajes": self.stats["total_mensajes"],
            "tiempo_respuesta_promedio": round(self.stats["tiempo_respuesta_promedio"], 3),
            "consultas_por_sistema": self.stats["consultas_por_sistema"],
            "consultas_por_problema": self.stats["consultas_por_problema"],
            "consultas_urgentes": self.stats["consultas_urgentes"],
            "derivaciones_agente": self.stats["derivaciones_agente"],
            "respuestas_automaticas": self.stats["respuestas_automaticas"],
            "fecha_actual": fecha_actual,
            "fecha_inicio": fecha_inicio,
            "start_date": start_date,
            "end_date": end_date,
            "consultas_satisfactorias": self.stats["consultas_satisfactorias"],
            "total_encuestas": self.stats["total_encuestas"]
        }

    def mostrar_ayuda(self):
        return """🔍 Bot de Mantenimiento MOC

Puedo ayudarte con:
- Problemas de arranque en sistemas
- Fallas de operación
- Mensajes de error
- Verificaciones de sistema
- Consultas de estado
- Soluciones rápidas para problemas comunes

Formato recomendado:
"[Sistema] de [Matrícula] [problema]"
Ejemplo: "APU del CC-AWN no arranca"

Comandos disponibles:
- ayuda: Muestra este mensaje
- ejemplos: Muestra ejemplos de uso
- agente: Conecta con un agente humano
- urgente: Marca tu caso como prioritario

¿En qué puedo ayudarte hoy?"""

    def mostrar_ejemplos(self):
        return """📝 Ejemplos de consultas:

1. Problemas de arranque:
- "APU no arranca"
- "El APU del CC-AWN no arranca"
- "Problema de arranque en APU"

2. Fallas de operación:
- "Motor 1 no funciona"
- "Falla en el tren de aterrizaje"
- "Sistema hidráulico inoperativo CC-BAW"

3. Mensajes de error:
- "Error en galley CC-COP"
- "Warning de APU en CC-AWN"
- "Luz de alerta en sistema eléctrico"

4. Verificaciones:
- "Revisar APU CC-BAW"
- "Verificar sistema eléctrico"
- "Check de tren de aterrizaje CC-COP"

5. Problemas específicos:
- "APU overheat"
- "Low oil pressure"
- "Hydraulic low level"
- "Problema con cargo door"

¿Cuál es tu consulta?"""

    def generar_respuesta_automatica(self, sistema, problema):
        """Genera una respuesta automática basada en el sistema y problema"""
        # Primero intentar obtener una respuesta del manual
        manual_response = None
        if hasattr(self, 'manual_knowledge'):
            manual_response = self.manual_knowledge.get_response(sistema, problema)
        
        # Si hay una respuesta en el manual, usarla
        if manual_response:
            return f"Según el manual de mantenimiento:\n\n{manual_response}\n\nSiguiendo estos pasos deberías resolver el problema. Si necesitas más información, escribe 'agente' para hablar con un especialista."
        
        # Si no hay respuesta en el manual, usar las respuestas predefinidas
        key = (sistema, problema)
        if key in self.respuestas_automaticas:
            respuesta_base = random.choice(self.respuestas_automaticas[key])
            # Añadir un cierre que indique que es una respuesta final
            return f"{respuesta_base}\n\nEspero que esto ayude a resolver tu problema. Si necesitas más asistencia, no dudes en proporcionar más detalles."
        
        # Si no hay respuesta predefinida, dar una respuesta genérica
        return (f"He detectado un problema de {problema} en el sistema {sistema}. "
                f"Para este tipo de situación, te recomiendo verificar lo siguiente:\n\n"
                f"1. Comprobar las conexiones y suministro eléctrico\n"
                f"2. Verificar si hay mensajes de error específicos\n"
                f"3. Revisar el estado de los componentes relacionados\n\n"
                f"Si el problema persiste, por favor proporciona más detalles o "
                f"escribe 'agente' para hablar con un especialista de mantenimiento.")

    def procesar_respuesta_encuesta(self, mensaje, id_usuario):
        """Procesa la respuesta de la encuesta de satisfacción"""
        respuesta_normalizada = mensaje.lower().strip()
        
        # Verificar si la respuesta es válida con una lista más amplia de posibles respuestas
        respuestas_positivas = ['si', 'sí', 's', 'yes', 'y', 'claro', 'por supuesto', 'afirmativo', 'correcto']
        respuestas_negativas = ['no', 'n', 'not', 'nope', 'negativo', 'incorrecto', 'para nada']
        
        if any(resp == respuesta_normalizada for resp in respuestas_positivas):
            satisfaccion = True
            respuesta = "¡Gracias por tu feedback positivo! Nos alegra haber podido ayudarte. Si necesitas ayuda con otra consulta, escribe 'nueva consulta'."
        elif any(resp == respuesta_normalizada for resp in respuestas_negativas):
            satisfaccion = False
            respuesta = "Lamentamos no haber podido resolver tu consulta. ¿Deseas que un agente humano te contacte? Responde 'agente' si es así, o 'nueva consulta' para intentar con otro problema."
        elif respuesta_normalizada == 'agente':
            # Si responde directamente "agente", iniciar recopilación de información
            self.contexto_actual[id_usuario]['en_encuesta'] = False
            self.contexto_actual[id_usuario]['encuesta_respondida'] = True
            return self.iniciar_recopilacion_info_agente(id_usuario, time.time())
        else:
            # Si la respuesta no es clara, volver a preguntar
            return "Por favor, responde Sí o No. ¿El problema o tu consulta fue resuelta?"
        
        # Actualizar estadísticas
        if 'consultas_satisfactorias' not in self.stats:
            self.stats['consultas_satisfactorias'] = 0
        
        if 'total_encuestas' not in self.stats:
            self.stats['total_encuestas'] = 0
        
        self.stats['total_encuestas'] += 1
        if satisfaccion:
            self.stats['consultas_satisfactorias'] += 1
        
        # Guardar estadísticas
        self.guardar_estadisticas()
        
        # Finalizar la encuesta y marcar que ya se ha respondido
        self.contexto_actual[id_usuario]['en_encuesta'] = False
        self.contexto_actual[id_usuario]['encuesta_respondida'] = True
        
        return respuesta

    def _es_respuesta_final(self, respuesta):
        """Determina si una respuesta parece ser la solución final a un problema"""
        # Palabras clave que indican que la respuesta es una solución completa
        palabras_solucion = [
            "siguiendo estos pasos", "esto debería resolver", "solución", 
            "procedimiento", "verifica", "comprueba", "si el problema persiste",
            "si necesitas más ayuda", "espero que esto ayude", "para servirte",
            "¿hay algo más", "¿necesitas algo más"
        ]
        
        # Verificar si la respuesta contiene alguna de las palabras clave
        respuesta_lower = respuesta.lower()
        for palabra in palabras_solucion:
            if palabra in respuesta_lower:
                return True
        
        # También podemos considerar respuestas largas como soluciones completas
        if len(respuesta) > 200:  # Si la respuesta es extensa
            return True
        
        return False

    def reiniciar_conversacion(self, id_usuario):
        """Reinicia el contexto de la conversación para un nuevo tema"""
        if id_usuario in self.contexto_actual:
            # Mantener solo el estado de la encuesta respondida
            encuesta_respondida = self.contexto_actual[id_usuario].get('encuesta_respondida', False)
            self.contexto_actual[id_usuario] = {'encuesta_respondida': encuesta_respondida}
        else:
            self.contexto_actual[id_usuario] = {}

    def manejar_tren_aterrizaje(self, id_usuario, problema, matricula=None):
        """Maneja específicamente casos relacionados con el tren de aterrizaje"""
        contexto = self.obtener_contexto(id_usuario)
        
        # Si ya tenemos la matrícula, dar la solución completa
        if matricula or contexto.get('matricula'):
            matricula_final = matricula or contexto.get('matricula')
            
            if problema == 'REVISAR':
                respuesta = (f"Para realizar un check del tren de aterrizaje en {matricula_final}, sigue estos pasos:\n\n"
                            f"1. Verifica visualmente la condición de los componentes del tren\n"
                            f"2. Comprueba la presión de los neumáticos (debe estar entre 180-210 PSI)\n"
                            f"3. Verifica que no haya fugas hidráulicas en los actuadores\n"
                            f"4. Comprueba el funcionamiento de las luces indicadoras\n"
                            f"5. Verifica la correcta extensión y retracción del tren\n\n"
                            f"Si encuentras alguna anomalía, regístrala en el libro de mantenimiento y notifica al equipo técnico.")
            elif problema == 'NO_FUNCIONA':
                respuesta = (f"Para problemas con el tren de aterrizaje que no funciona en {matricula_final}, verifica lo siguiente:\n\n"
                            f"1. Comprueba el sistema hidráulico (presión y nivel de fluido)\n"
                            f"2. Verifica los breakers relacionados con el sistema del tren\n"
                            f"3. Inspecciona los actuadores y mecanismos de bloqueo\n"
                            f"4. Comprueba el funcionamiento del sistema de emergencia\n"
                            f"5. Verifica los sensores de posición del tren\n\n"
                            f"Si el problema persiste, considera utilizar el procedimiento de extensión de emergencia y contacta al equipo de mantenimiento.")
            else:
                respuesta = (f"Para problemas con el tren de aterrizaje en {matricula_final}, verifica lo siguiente:\n\n"
                            f"1. Comprueba el sistema hidráulico\n"
                            f"2. Verifica los componentes mecánicos\n"
                            f"3. Inspecciona los indicadores y sensores\n\n"
                            f"Si necesitas asistencia específica, proporciona más detalles sobre el problema exacto.")
            
            # Actualizar contexto
            contexto['sistema'] = 'TREN'
            contexto['problema'] = problema
            contexto['matricula'] = matricula_final
            self.contexto_actual[id_usuario] = contexto
            
            return respuesta
        else:
            # Si no tenemos la matrícula, pedirla
            contexto['sistema'] = 'TREN'
            contexto['problema'] = problema
            self.contexto_actual[id_usuario] = contexto
            
            return f"Detecto un problema con el tren de aterrizaje. ¿Podrías indicarme la matrícula de la aeronave?"

    def manejar_sistema_electrico(self, id_usuario, problema, matricula=None):
        """Maneja específicamente casos relacionados con el sistema eléctrico"""
        contexto = self.obtener_contexto(id_usuario)
        
        # Si ya tenemos la matrícula, dar la solución completa
        if matricula or contexto.get('matricula'):
            matricula_final = matricula or contexto.get('matricula')
            
            if problema == 'REVISAR':
                respuesta = (f"Para verificar el sistema eléctrico en {matricula_final}, sigue estos pasos:\n\n"
                            f"1. Comprueba el estado de las baterías y su carga\n"
                            f"2. Verifica el funcionamiento de los generadores principales\n"
                            f"3. Inspecciona el panel de breakers y asegúrate de que todos estén en posición correcta\n"
                            f"4. Comprueba las conexiones y cableado visible\n"
                            f"5. Verifica el funcionamiento de los sistemas de iluminación\n\n"
                            f"Si encuentras alguna anomalía, documéntala y notifica al equipo de mantenimiento.")
            elif problema == 'NO_FUNCIONA':
                respuesta = (f"Para problemas con el sistema eléctrico en {matricula_final}, verifica lo siguiente:\n\n"
                            f"1. Comprueba si los generadores están funcionando correctamente\n"
                            f"2. Verifica el estado de las baterías y su conexión\n"
                            f"3. Inspecciona los breakers relacionados con el sistema afectado\n"
                            f"4. Comprueba las conexiones y busca signos de daño en el cableado\n"
                            f"5. Verifica si el APU puede proporcionar energía eléctrica de respaldo\n\n"
                            f"Si el problema persiste después de estas verificaciones, contacta al equipo de mantenimiento para una inspección más detallada.")
            else:
                respuesta = (f"Para problemas con el sistema eléctrico en {matricula_final}, verifica lo siguiente:\n\n"
                            f"1. Comprueba las baterías y generadores\n"
                            f"2. Verifica los breakers y conexiones\n"
                            f"3. Inspecciona el cableado visible\n\n"
                            f"Si necesitas asistencia específica, proporciona más detalles sobre el problema exacto.")
            
            # Actualizar contexto
            contexto['sistema'] = 'ELECTRICO'
            contexto['problema'] = problema
            contexto['matricula'] = matricula_final
            self.contexto_actual[id_usuario] = contexto
            
            return respuesta
        else:
            # Si no tenemos la matrícula, pedirla
            contexto['sistema'] = 'ELECTRICO'
            contexto['problema'] = problema
            self.contexto_actual[id_usuario] = contexto
            
            return f"Detecto un problema con el sistema eléctrico. ¿Podrías indicarme la matrícula de la aeronave?"

    def manejar_reset_sistema(self, id_usuario, sistema=None):
        """Maneja consultas sobre cómo realizar un reset de un sistema"""
        contexto = self.obtener_contexto(id_usuario)
        
        # Si no se especifica sistema, intentar obtenerlo del contexto
        if not sistema:
            sistema = contexto.get('sistema')
        
        # Si aún no tenemos sistema, preguntar
        if not sistema:
            return "¿Para qué sistema necesitas realizar un reset? (APU, Eléctrico, etc.)"
        
        # Respuestas específicas según el sistema
        if sistema.upper() == 'APU':
            respuesta = (
                "Para realizar un reset del sistema APU, sigue estos pasos:\n\n"
                "1. Asegúrate de que el APU esté completamente apagado (interruptor en posición OFF)\n"
                "2. Localiza el panel de breakers relacionados con el APU\n"
                "3. Identifica los breakers específicos del APU (normalmente etiquetados como 'APU CONTROL', 'APU STARTER', etc.)\n"
                "4. Desconecta (pull) estos breakers y espera 30 segundos\n"
                "5. Vuelve a conectar (push) los breakers en el mismo orden en que los desconectaste\n"
                "6. Espera 2 minutos para que el sistema se reinicie completamente\n"
                "7. Intenta arrancar el APU siguiendo el procedimiento normal\n\n"
                "Si después del reset el APU sigue sin funcionar, será necesario contactar al equipo de mantenimiento para una inspección más detallada."
            )
        elif sistema.upper() == 'ELECTRICO' or sistema.upper() == 'ELÉCTRICO':
            respuesta = (
                "Para realizar un reset del sistema eléctrico, sigue estos pasos:\n\n"
                "1. Asegúrate de que todos los sistemas no esenciales estén apagados\n"
                "2. Localiza el panel de breakers principal\n"
                "3. Identifica los breakers del sistema eléctrico afectado\n"
                "4. Desconecta (pull) estos breakers y espera 60 segundos\n"
                "5. Vuelve a conectar (push) los breakers\n"
                "6. Reinicia los sistemas afectados uno por uno\n\n"
                "Si el problema persiste después del reset, contacta al equipo de mantenimiento."
            )
        elif sistema.upper() == 'TREN' or 'ATERRIZAJE' in sistema.upper():
            respuesta = (
                "Para realizar un reset del sistema de tren de aterrizaje, sigue estos pasos:\n\n"
                "1. Asegúrate de que la aeronave esté en tierra y con los frenos aplicados\n"
                "2. Localiza el panel de control hidráulico y eléctrico relacionado con el tren\n"
                "3. Desconecta (pull) los breakers específicos del sistema de tren\n"
                "4. Espera 60 segundos para que el sistema se descargue completamente\n"
                "5. Vuelve a conectar (push) los breakers\n"
                "6. Verifica el funcionamiento del sistema mediante las luces indicadoras\n\n"
                "Nota: Este procedimiento debe realizarse siguiendo el manual de mantenimiento específico de la aeronave."
            )
        else:
            respuesta = (
                f"Para realizar un reset del sistema {sistema}, generalmente debes seguir estos pasos:\n\n"
                f"1. Consulta el manual de mantenimiento específico para {sistema}\n"
                f"2. Localiza los breakers relacionados con el sistema\n"
                f"3. Desconecta (pull) los breakers específicos\n"
                f"4. Espera el tiempo recomendado (generalmente 30-60 segundos)\n"
                f"5. Vuelve a conectar (push) los breakers\n"
                f"6. Reinicia el sistema siguiendo el procedimiento normal\n\n"
                f"Para instrucciones más detalladas, consulta el manual de mantenimiento de la aeronave."
            )
        
        # Actualizar contexto para mantener el tema de la conversación
        contexto['ultimo_tema'] = f"reset_{sistema.lower()}"
        self.contexto_actual[id_usuario] = contexto
        
        return respuesta

    def manejar_mensaje_corto(self, mensaje, id_usuario):
        """Maneja mensajes cortos o ambiguos"""
        contexto = self.obtener_contexto(id_usuario)
        
        # Verificar si tenemos información en el contexto
        sistema = contexto.get('sistema')
        problema = contexto.get('problema')
        matricula = contexto.get('matricula')
        
        if sistema and problema and not matricula:
            # Si ya sabemos sistema y problema pero no matrícula
            return f"Para ayudarte con el problema de {problema} en {sistema}, necesito la matrícula de la aeronave. ¿Podrías proporcionarla?"
        
        elif sistema and not problema:
            # Si ya sabemos el sistema pero no el problema
            return f"Entiendo que mencionas el sistema {sistema}. ¿Qué problema específico estás experimentando?"
        
        elif problema and not sistema:
            # Si ya sabemos el problema pero no el sistema
            return f"Entiendo que hay un problema de {problema}. ¿En qué sistema específico de la aeronave?"
        
        elif sistema and problema and matricula:
            # Si ya tenemos toda la información, generar respuesta
            if sistema == 'APU' and problema == 'NO_ARRANCA':
                return self.manejar_apu_no_arranca(id_usuario, matricula)
            elif sistema == 'APU' and problema == 'NO_FUNCIONA':
                return self.manejar_apu_no_funciona(id_usuario, matricula)
            elif sistema == 'TREN':
                return self.manejar_tren_aterrizaje(id_usuario, problema, matricula)
            elif sistema == 'ELECTRICO':
                return self.manejar_sistema_electrico(id_usuario, problema, matricula)
        
        # Si no tenemos suficiente información
        return ("Por favor, proporciona más detalles sobre tu consulta. Necesito saber:\n"
                "- El sistema afectado (APU, Motor, Tren, etc.)\n"
                "- El problema (no arranca, no funciona, error, etc.)\n"
                "- La matrícula de la aeronave\n\n"
                "Ejemplo: 'El APU del CC-AWN no arranca'")

    def detectar_cambio_tema(self, mensaje, id_usuario):
        """Detecta si el mensaje indica un cambio de tema en la conversación"""
        contexto = self.obtener_contexto(id_usuario)
        
        # Si no hay contexto previo, no hay cambio de tema
        if not contexto.get('sistema') and not contexto.get('problema'):
            return False
        
        # Detectar sistema y problema en el mensaje actual
        sistema_actual, problema_actual, _ = self.detectar_sistema_y_problema(mensaje)
        
        # Si detectamos un sistema o problema diferente al del contexto, es un cambio de tema
        if sistema_actual and sistema_actual != contexto.get('sistema'):
            return True
        
        if problema_actual and problema_actual != contexto.get('problema'):
            return True
        
        return False

    def es_mensaje_despedida(self, mensaje):
        """Detecta si el mensaje es una despedida o indica que no se necesita más ayuda"""
        mensaje_lower = mensaje.lower()
        
        # Lista ampliada de frases que indican que el usuario no necesita más ayuda
        frases_despedida = [
            'no', 'no gracias', 'no necesito más ayuda', 'no hay más', 'nada más', 'es todo',
            'nada mas', 'nada mas gracias', 'eso es todo', 'listo', 'terminamos', 'gracias',
            'muchas gracias', 'eso sería todo', 'no hay nada más', 'no hay nada mas',
            'contactar', 'contáctar', 'contactame', 'contáctame'
        ]
        
        # Verificar si alguna de las frases está en el mensaje
        for frase in frases_despedida:
            if frase in mensaje_lower:
                return True
        
        return False

    def procesar_recopilacion_info_agente(self, mensaje, id_usuario):
        """Procesa la información recopilada para derivar a un agente"""
        contexto = self.obtener_contexto(id_usuario)
        paso_actual = contexto.get('paso_recopilacion')
        
        # Procesar según el paso actual
        if paso_actual == 'sistema':
            # Guardar sistema
            sistema, _, _ = self.detectar_sistema_y_problema(mensaje)
            if sistema:
                contexto['sistema'] = sistema
            else:
                contexto['sistema'] = mensaje.upper()  # Si no detectamos, guardar lo que escribió
            
            # Verificar si ya tenemos problema
            if contexto.get('problema'):
                # Si ya tenemos problema, preguntar matrícula
                if not contexto.get('matricula'):
                    contexto['paso_recopilacion'] = 'matricula'
                    self.contexto_actual[id_usuario] = contexto
                    return "Por favor, indica la matrícula de la aeronave (formato CC-XXX):"
                else:
                    # Si ya tenemos matrícula, preguntar error
                    contexto['paso_recopilacion'] = 'error'
                    self.contexto_actual[id_usuario] = contexto
                    return "¿Hay algún mensaje de error específico en la pantalla? Por favor, descríbelo o indica 'ninguno':"
            else:
                # Si no tenemos problema, preguntar problema
                contexto['paso_recopilacion'] = 'problema'
                self.contexto_actual[id_usuario] = contexto
                return "Por favor, describe el problema específico:"
        
        elif paso_actual == 'problema':
            # Guardar problema
            _, problema, _ = self.detectar_sistema_y_problema(mensaje)
            if problema:
                contexto['problema'] = problema
            else:
                contexto['problema'] = mensaje  # Si no detectamos, guardar lo que escribió
            
            # Verificar si ya tenemos matrícula
            if not contexto.get('matricula'):
                contexto['paso_recopilacion'] = 'matricula'
                self.contexto_actual[id_usuario] = contexto
                return "Por favor, indica la matrícula de la aeronave (formato CC-XXX):"
            else:
                # Si ya tenemos matrícula, preguntar error
                contexto['paso_recopilacion'] = 'error'
                self.contexto_actual[id_usuario] = contexto
                return "¿Hay algún mensaje de error específico en la pantalla? Por favor, descríbelo o indica 'ninguno':"
        
        elif paso_actual == 'matricula':
            # Detectar matrícula
            _, _, matricula = self.detectar_sistema_y_problema(mensaje)
            if matricula:
                contexto['matricula'] = matricula
            else:
                # Si no detectamos formato CC-XXX, intentar formatear
                if re.match(r'^[a-zA-Z]{2}[a-zA-Z0-9]{3}$', mensaje.strip()):
                    contexto['matricula'] = f"{mensaje[:2].upper()}-{mensaje[2:].upper()}"
                else:
                    contexto['matricula'] = mensaje.upper()  # Guardar lo que escribió
            
            # Preguntar error
            contexto['paso_recopilacion'] = 'error'
            self.contexto_actual[id_usuario] = contexto
            return "¿Hay algún mensaje de error específico en la pantalla? Por favor, descríbelo o indica 'ninguno':"
        
        elif paso_actual == 'error':
            # Guardar error
            if mensaje.lower() != 'ninguno' and mensaje.lower() != 'no' and mensaje.lower() != 'n/a':
                contexto['error_especifico'] = mensaje
            else:
                contexto['error_especifico'] = "Ninguno reportado"
            
            # Preguntar fase de vuelo
            contexto['paso_recopilacion'] = 'fase_vuelo'
            self.contexto_actual[id_usuario] = contexto
            return "¿En qué fase se presentó el problema? (despegue, aterrizaje, crucero, taxeo, otra):"
        
        elif paso_actual == 'fase_vuelo':
            # Guardar fase de vuelo
            contexto['fase_vuelo'] = mensaje
            
            # Preguntar ubicación
            contexto['paso_recopilacion'] = 'ubicacion'
            self.contexto_actual[id_usuario] = contexto
            return "¿Dónde está físicamente la aeronave ahora? (aeropuerto o ubicación):"
        
        elif paso_actual == 'ubicacion':
            # Guardar ubicación
            contexto['ubicacion'] = mensaje
            
            # Finalizar recopilación
            contexto['recopilando_info_agente'] = False
            
            # Generar resumen para el agente
            sistema = contexto.get('sistema', 'No especificado')
            problema = contexto.get('problema', 'No especificado')
            matricula = contexto.get('matricula', 'No especificada')
            error = contexto.get('error_especifico', 'Ninguno reportado')
            fase = contexto.get('fase_vuelo', 'No especificada')
            ubicacion = contexto.get('ubicacion', 'No especificada')
            
            resumen = (
                "Gracias por proporcionar toda la información. Un agente especializado te contactará pronto.\n\n"
                "Resumen de la información:\n"
                f"- Sistema: {sistema}\n"
                f"- Problema: {problema}\n"
                f"- Matrícula: {matricula}\n"
                f"- Error específico: {error}\n"
                f"- Fase de vuelo: {fase}\n"
                f"- Ubicación actual: {ubicacion}\n\n"
                "Esta información ha sido enviada al equipo de mantenimiento. ¿Hay algo más que quieras añadir?"
            )
            
            # Marcar como derivado a agente en estadísticas
            self.stats['derivaciones_agente'] += 1
            self.guardar_estadisticas()
            
            self.contexto_actual[id_usuario] = contexto
            return resumen
        
        else:
            # Si llegamos aquí, algo salió mal, reiniciar el proceso
            return self.iniciar_recopilacion_info_agente(id_usuario, time.time())

    def iniciar_recopilacion_info_agente(self, id_usuario, tiempo_inicio):
        """Inicia el proceso de recopilación de información para derivar a un agente"""
        contexto = self.obtener_contexto(id_usuario)
        
        # Marcar que estamos recopilando información
        contexto['recopilando_info_agente'] = True
        contexto['paso_recopilacion'] = 1
        
        # Guardar información que ya tenemos
        sistema = contexto.get('sistema')
        problema = contexto.get('problema')
        matricula = contexto.get('matricula')
        
        # Construir mensaje inicial
        mensaje = "Entendido. Para poder derivarte con un agente especializado, necesito recopilar algunos datos adicionales.\n\n"
        
        if sistema:
            mensaje += f"Sistema afectado: {sistema}\n"
        else:
            mensaje += "Por favor, indica el sistema afectado (APU, Motor, Tren, etc.):\n"
            contexto['paso_recopilacion'] = 'sistema'
            self.contexto_actual[id_usuario] = contexto
            self.registrar_respuesta(id_usuario, mensaje, tiempo_inicio)
            return mensaje
        
        if problema:
            mensaje += f"Problema: {problema}\n"
        else:
            mensaje += "Por favor, describe el problema específico:\n"
            contexto['paso_recopilacion'] = 'problema'
            self.contexto_actual[id_usuario] = contexto
            self.registrar_respuesta(id_usuario, mensaje, tiempo_inicio)
            return mensaje
        
        if matricula:
            mensaje += f"Matrícula: {matricula}\n\n"
            # Si ya tenemos sistema, problema y matrícula, pasar a la siguiente pregunta
            mensaje += "¿Hay algún mensaje de error específico en la pantalla? Por favor, descríbelo o indica 'ninguno':"
            contexto['paso_recopilacion'] = 'error'
        else:
            mensaje += "Por favor, indica la matrícula de la aeronave (formato CC-XXX):"
            contexto['paso_recopilacion'] = 'matricula'
        
        self.contexto_actual[id_usuario] = contexto
        self.registrar_respuesta(id_usuario, mensaje, tiempo_inicio)
        return mensaje