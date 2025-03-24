import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO, emit
import threading
import logging
from flask import request

# Configuration
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, 
                  cors_allowed_origins="*",
                  engineio_logger=True,
                  logger=True,
                  async_mode='eventlet')

# État global
clients = {"sender": None, "receiver": None}
pending_requests = 0
lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connecté: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    with lock:
        if clients['sender'] == request.sid:
            clients['sender'] = None
            logger.info("Sender déconnecté")
        elif clients['receiver'] == request.sid:
            clients['receiver'] = None
            logger.info("Receiver déconnecté")

@socketio.on('register')
def handle_register(data):
    with lock:
        client_type = data.get('type')
        if client_type == 'session2':
            clients['sender'] = request.sid
            logger.info(f"Sender enregistré: {request.sid}")
        elif client_type == 'session1':
            clients['receiver'] = request.sid
            logger.info(f"Receiver enregistré: {request.sid}")

@socketio.on('request_more_data')
def handle_data_request(data):
    global pending_requests
    count = data.get('count', 50)  # Valeur par défaut
    
    with lock:
        if pending_requests > 2:
            logger.warning("Trop de requêtes en attente")
            return
            
        if clients['sender']:
            pending_requests += 1
            emit('send_chunks', {'count': count}, room=clients['sender'])
            logger.info(f"Demande de {count} chunks envoyée au sender")
        else:
            logger.warning("Aucun sender disponible")

@socketio.on('chunks_sent')
def handle_chunks_sent():
    global pending_requests
    with lock:
        if pending_requests > 0:
            pending_requests -= 1
    logger.info("Chunks livrés, requêtes en attente: {pending_requests}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)