from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from flask_session import Session
from flask_socketio import SocketIO, emit
import numpy as np
import datetime
import numpy as np
from scipy.io.wavfile import write
import os
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SESSION_TYPE'] = 'filesystem'  # Use armazenamento em arquivo
app.config['SESSION_USE_SIGNER'] = False  # Não use assinatura de sessão (desativar cookies)

Session(app)
socketio = SocketIO(app, logger=True, engineio_logger=True, max_http_buffer_size=1000000000)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/set_username', methods=['POST'])
def set_username():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    session['username'] = username
    session['password'] = password
    session['expiration'] = datetime.datetime.now() + datetime.timedelta(seconds=5)
    return jsonify({'message': 'Username set successfully'})


@app.route('/chat')
def chat():
    if 'username' in session:
        print(session)
        client_ip = request.remote_addr
        return render_template('chat.html', username=session['username'], ip=f'{client_ip}', password=session['password'])
    else:
        print('username not in session, redirecting for /login')
        return redirect(url_for('login'))


@app.route('/api/download-wav', methods=['POST'])
def download_wav():
    data = request.json
    filename = f'audio{data["id"]}.wav'
    filepath = f'audios/{filename}'

    audioContent = np.array(data['audioContent'])
    # Ajusta os valores para o intervalo de -32768 a 32767 (formato int16)
    array_audio_normalizado_int16 = (audioContent * 32767).astype(np.int16)

    # Crie uma resposta BytesIO em vez de salvar o arquivo no sistema de arquivos
    wav_bytesio = BytesIO()

    # Use a função write corretamente
    write(wav_bytesio, 48000, array_audio_normalizado_int16)
    
    response_headers = {
        'Content-Type': 'audio/wav',
        'Content-Disposition': f'attachment; filename={filename}',
    }

    write(wav_bytesio, 48000, array_audio_normalizado_int16)
    wav_bytes = wav_bytesio.getvalue()
    # Use make_response e send_file juntos
    response = make_response(wav_bytes)

    # Adicione cabeçalhos à resposta
    for header, value in response_headers.items():
        response.headers[header] = value

    return response


@socketio.on('clientMessage')
def handle_message(data):
    print(len(data['audioContent']))
    print(f'Mensagem emitida por: {data["senderName"]}')
    emit('serverMessage', data, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', allow_unsafe_werkzeug=False)
