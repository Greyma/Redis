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
    logger.info(f"✓ Client connecté: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    with lock:
        if clients['sender'] == request.sid:
            clients['sender'] = None
            logger.info("✗ Sender déconnecté")
        elif clients['receiver'] == request.sid:
            clients['receiver'] = None
            logger.info("✗ Receiver déconnecté")
        else:
            logger.info(f"✗ Client inconnu déconnecté: {request.sid}")

@socketio.on('register')
def handle_register(data):
    with lock:
        client_type = data.get('type')
        if client_type == 'session2':
            clients['sender'] = request.sid
            logger.info(f"✓ Sender (Session 2) enregistré: {request.sid}")
        elif client_type == 'session1':
            clients['receiver'] = request.sid
            logger.info(f"✓ Receiver (Session 1) enregistré: {request.sid}")
            # Si le sender est déjà connecté, lancer une demande initiale
            if clients['sender']:
                emit('send_chunks', {'count': 50}, room=clients['sender'])
                logger.info("↳ Demande initiale de 50 chunks envoyée au sender")

@socketio.on('request_more_data')
def handle_data_request(data):
    global pending_requests
    count = data.get('count', 50)  # Valeur par défaut
    
    with lock:
        if pending_requests >= 2:  # Changé > 2 à >= 2 pour cohérence
            logger.warning("⚠ Trop de requêtes en attente, demande ignorée")
            return
            
        if clients['sender']:
            pending_requests += 1
            emit('send_chunks', {'count': count}, room=clients['sender'])
            logger.info(f"→ Demande de {count} chunks envoyée au sender ({clients['sender']})")
        else:
            logger.warning("⚠ Aucun sender disponible pour répondre à la demande")

@socketio.on('receive_chunk')
def handle_receive_chunk(data):
    with lock:
        if request.sid == clients['sender'] and clients['receiver']:
            emit('receive_chunk', data, room=clients['receiver'])
            logger.info(f"✓ Chunk relayé de sender ({request.sid}) à receiver ({clients['receiver']})")
        elif not clients['receiver']:
            logger.warning("⚠ Chunk reçu mais aucun receiver connecté")
        else:
            logger.warning(f"⚠ Chunk reçu d'un client inconnu: {request.sid}")

@socketio.on('chunks_sent')
def handle_chunks_sent():
    global pending_requests
    with lock:
        if pending_requests > 0:
            pending_requests -= 1
        logger.info(f"✓ Chunks livrés, requêtes en attente: {pending_requests}")

if __name__ == '__main__':
    logger.info("→ Démarrage du serveur sur port 10000...")
    socketio.run(app, host='0.0.0.0', port=10000)