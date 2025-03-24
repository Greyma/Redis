from flask import Flask, request
from flask_socketio import SocketIO, emit
import pickle

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Permet les connexions depuis Kaggle

# Gestion des connexions WebSocket
clients = {"session2": None, "session1": None}

@socketio.on('connect')
def handle_connect():
    print("Client connecté")

@socketio.on('register')
def handle_register(data):
    client_type = data.get('type')
    if client_type == 'session2':
        clients['session2'] = request.sid  # ID de la Session 2
        print("Session 2 enregistrée")
    elif client_type == 'session1':
        clients['session1'] = request.sid  # ID de la Session 1
        print("Session 1 enregistrée")

@socketio.on('send_data')
def handle_send_data(data):
    if clients['session1']:  # Si Session 1 est connectée
        # Relayer les données directement à Session 1
        emit('receive_data', data, to=clients['session1'])
        print("Données relayées de Session 2 à Session 1")
    else:
        emit('error', {'message': 'Session 1 non connectée'}, to=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)