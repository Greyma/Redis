from flask import Flask, request
from flask_socketio import SocketIO, emit
import pickle
from collections import deque

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {"session2": None, "session1": None}
pending_data = deque()  # File d’attente pour les données

@socketio.on('connect')
def handle_connect():
    print("Client connecté")

@socketio.on('register')
def handle_register(data):
    client_type = data.get('type')
    if client_type == 'session2':
        clients['session2'] = request.sid
        print("Session 2 enregistrée, SID :", request.sid)
    elif client_type == 'session1':
        clients['session1'] = request.sid
        print("Session 1 enregistrée, SID :", request.sid)
        # Envoyer les données en attente
        while pending_data and clients['session1']:
            emit('receive_data', pending_data.popleft(), to=clients['session1'])
            print("Données en attente relayées à Session 1")

@socketio.on('send_data')
def handle_send_data(data):
    print("Événement send_data reçu, taille des données :", len(data))
    if clients['session1']:
        emit('receive_data', data, to=clients['session1'])
        print("Données relayées de Session 2 à Session 1")
    else:
        pending_data.append(data)
        print("Session 1 non connectée, données mises en attente, état des clients :", clients)
        emit('error', {'message': 'Session 1 non connectée, données en attente'}, to=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)