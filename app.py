from flask import Flask, request
from flask_socketio import SocketIO, emit
import pickle
from collections import deque
import psutil

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {"session2": None, "session1": None}
pending_data = deque(maxlen=4)  # Limite à ~400 Mo

@socketio.on('connect')
def handle_connect():
    print("Client connecté, RAM utilisée :", psutil.virtual_memory().percent, "%")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid == clients['session2']:
        clients['session2'] = None
        print("Session 2 déconnectée")
    elif sid == clients['session1']:
        clients['session1'] = None
        print("Session 1 déconnectée")

@socketio.on('register')
def handle_register(data):
    client_type = data.get('type')
    if client_type == 'session2':
        clients['session2'] = request.sid
        print("Session 2 enregistrée, SID :", request.sid)
    elif client_type == 'session1':
        clients['session1'] = request.sid
        print("Session 1 enregistrée, SID :", request.sid)
        while pending_data and clients['session1']:
            emit('receive_data', pending_data.popleft(), to=clients['session1'])
            print("Données en attente relayées à Session 1")

@socketio.on('send_data')
def handle_send_data(data):
    print("Événement send_data reçu, taille :", len(data) / (1024 * 1024), "Mo")
    print("RAM utilisée :", psutil.virtual_memory().percent, "%")
    if clients['session1']:
        emit('receive_data', data, to=clients['session1'])
        print("Données relayées de Session 2 à Session 1")
    else:
        pending_data.append(data)
        print("Session 1 non connectée, données mises en attente, file :", len(pending_data))
        emit('error', {'message': 'Session 1 non connectée, données en attente'}, to=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)