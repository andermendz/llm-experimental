# Import necessary libraries
from flask import Flask, request, render_template
from flask_socketio import SocketIO
from g4f.client import Client
import traceback
import time

# Initialize Flask app and G4F client
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
client = Client()

# Define the function for generating creative writing prompts
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/stream', methods=['POST'])
def stream_response():
    try:
        user_message = request.form.get('message', 'Hello!')
        print(f"Received message: {user_message}")
        
        # Create the chat completion with streaming
        response = ""
        stream = client.chat.completions.create(
            model="",  # Changed to a more reliable model
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_message}
            ],
            stream=True
        )
        
        print("Stream created, starting to process chunks...")
        
        for chunk in stream:
            try:
                partial_response = chunk.choices[0].delta.content or ""
                if partial_response:
                    response += partial_response
                    print(f"Emitting chunk: {partial_response}")
                    socketio.emit('stream_response', {'data': partial_response})
                    socketio.sleep(0)  # Allow other events to be processed
            except Exception as chunk_error:
                print(f"Error processing chunk: {chunk_error}")
                traceback.print_exc()
                continue

        print("Stream completed successfully")
        return {"status": "complete", "full_response": response}
    except Exception as e:
        error_msg = f"Error in stream_response: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {"status": "error", "message": str(e)}, 500

# Run the Flask app
if __name__ == '__main__':
    socketio.run(app, debug=True)