import eventlet
eventlet.monkey_patch()  # Doit être en tout premier !

from flask import Flask , request
from flask_socketio import SocketIO
import threading
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   engineio_logger=True,
                   logger=True,
                   async_mode='eventlet')

clients = {"sender": None, "receiver": None}
client_lock = threading.Lock()

@app.before_first_request
def setup():
    logger.info("Server setup complete")

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client {request.sid} connected")

@socketio.on('disconnect')
def handle_disconnect():
    with client_lock:
        if clients['sender'] == request.sid:
            clients['sender'] = None
            logger.info("Sender disconnected")
        elif clients['receiver'] == request.sid:
            clients['receiver'] = None
            logger.info("Receiver disconnected")

@socketio.on('register')
def handle_register(data):
    with client_lock:
        client_type = data.get('type')
        if client_type == 'session2' and clients['sender'] is None:
            clients['sender'] = request.sid
            logger.info(f"Sender registered (SID: {request.sid})")
            if clients['receiver']:
                socketio.emit('sender_ready', to=clients['receiver'])
                
        elif client_type == 'session1' and clients['receiver'] is None:
            clients['receiver'] = request.sid
            logger.info(f"Receiver registered (SID: {request.sid})")
            if clients['sender']:
                socketio.emit('receiver_ready', to=clients['sender'])

if __name__ == '__main__':
    socketio.run(app, 
                host='0.0.0.0', 
                port=10000, 
                debug=True, 
                use_reloader=False,
                log_output=True)