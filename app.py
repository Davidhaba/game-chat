from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app)
rooms = {}
usernames = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_or_join')
def handle_create_or_join(data):
    username = data.get('username', 'Anonymous')
    room = data['room']
    password = data.get('password', '')

    if room in rooms:
        if rooms[room]['password'] and rooms[room]['password'] != password:
            emit('password_incorrect', 'Invalid password!')
            return
    else:
        rooms[room] = {'password': password}

    join_room(room)
    usernames[request.sid] = {'room': room, 'username': username}
    emit('message', {'username': username, 'msg': f'joined the room {room}', 'color': 'green'}, room=room)
    emit('room_list', list(rooms), broadcast=True)
    emit('room_joined', {'room': room})

@socketio.on('message')
def handle_message(data):
    msg = data['msg']
    room = data['room']
    username = data.get('username', 'Anonymous')
    emit('message', {'username': username + ":", 'msg': msg, 'color': 'black'}, room=room)

@socketio.on('get_rooms')
def handle_request_room_list():
    emit('room_list', list(rooms))

@socketio.on('get_connections')
def handle_request_room_list():
    emit('get_connections', list(usernames))

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in usernames:
        room = usernames[user_id]['room']
        username = usernames[user_id]['username']
        emit('message', {'username': username, 'msg': f'left the room {room}', 'color': 'red'}, room=room)
        del usernames[user_id]
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80)
