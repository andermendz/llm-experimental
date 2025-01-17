# Import necessary libraries
from flask import Flask, request, render_template, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from g4f.client import Client
import traceback
import time
import secrets
from threading import Lock

# Initialize Flask app and G4F client
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
client = Client()

# Thread lock for thread-safe operations
thread_lock = Lock()

# Keep track of active clients and their responses
active_clients = {}

@app.route('/')
def index():
    if 'client_id' not in session:
        session['client_id'] = secrets.token_hex(8)
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    client_id = session.get('client_id', secrets.token_hex(8))
    session['client_id'] = client_id  # Ensure client_id is in session
    join_room(client_id)  # Join a room specific to this client
    with thread_lock:
        active_clients[client_id] = {
            "connected": True,
            "sid": request.sid
        }
    print(f'Client {client_id} connected with sid {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    client_id = session.get('client_id')
    if client_id:
        with thread_lock:
            if client_id in active_clients:
                del active_clients[client_id]
        leave_room(client_id)
        print(f'Client {client_id} disconnected')

@app.route('/stream', methods=['POST'])
def stream_response():
    client_id = session.get('client_id')
    if not client_id:
        return {"status": "error", "message": "No session ID"}, 400

    try:
        user_message = request.form.get('message', 'Hello!')
        print(f"Received message from client {client_id}: {user_message}")
        
        response = ""
        
        # Create a new G4F client for each request to avoid conflicts
        request_client = Client()
        stream = request_client.chat.completions.create(
            model="gemini-1.5-pro",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_message}
            ],
            stream=True
        )
        
        print(f"Stream created for client {client_id}, starting to process chunks...")
        
        for chunk in stream:
            # Check if client is still connected
            with thread_lock:
                if client_id not in active_clients:
                    print(f"Client {client_id} disconnected during streaming")
                    break
                    
            try:
                partial_response = chunk.choices[0].delta.content or ""
                if partial_response:
                    response += partial_response
                    # Emit to specific client room
                    socketio.emit('stream_response', 
                                {'data': partial_response, 'client_id': client_id}, 
                                room=client_id)
            except Exception as chunk_error:
                print(f"Error processing chunk for client {client_id}: {chunk_error}")
                traceback.print_exc()
                continue

        print(f"Stream completed successfully for client {client_id}")
        return {"status": "complete", "full_response": response}
    except Exception as e:
        error_msg = f"Error in stream_response for client {client_id}: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    socketio.run(app, debug=True)