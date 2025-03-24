from flask import Flask , request
from flask_socketio import SocketIO
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {"sender": None, "receiver": None}
buffer_lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    print(f"Client {request.sid} connecté")

@socketio.on('disconnect')
def handle_disconnect():
    if clients['sender'] == request.sid:
        clients['sender'] = None
    elif clients['receiver'] == request.sid:
        clients['receiver'] = None

@socketio.on('register')
def handle_register(data):
    with buffer_lock:
        if data['type'] == 'session2':
            clients['sender'] = request.sid
            print("Sender (Session2) enregistré")
        elif data['type'] == 'session1':
            clients['receiver'] = request.sid
            print("Receiver (Session1-GPU) enregistré")
            # Autoriser l'envoi initial
            socketio.emit('receiver_ready', room=clients['sender'])

@socketio.on('request_more_data')
def handle_data_request(count):
    with buffer_lock:
        if clients['sender']:
            socketio.emit('send_chunks', {'count': count}, room=clients['sender'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)