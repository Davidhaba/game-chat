from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_or_join')
def handle_create_or_join(data):
    username = data.get('username', 'Анонім')
    room = data['room']
    password = data.get('password', '')

    if room in rooms:
        if rooms[room]['password'] and rooms[room]['password'] != password:
            emit('password_incorrect', 'Невірний пароль!')
            return
    else:
        rooms[room] = {'password': password}

    join_room(room)
    emit('message', {'username': username, 'msg': f'приєднався до кімнати {room}', 'color': 'green'}, room=room)
    emit('room_list', [{'name': room} for room in rooms], broadcast=True)
    emit('room_joined', {'room': room})

@socketio.on('message')
def handle_message(data):
    msg = data['msg']
    room = data['room']
    username = data.get('username', 'Анонім')
    emit('message', {'username': username + ":", 'msg': msg, 'color': 'black'}, room=room)

@socketio.on('get_rooms')
def handle_request_room_list():
    emit('room_list', list(rooms))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80)
