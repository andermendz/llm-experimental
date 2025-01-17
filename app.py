# Import necessary libraries
from g4f.client import Client
from flask import Flask, render_template, request, jsonify

# Initialize Flask app and G4F client
app = Flask(__name__)
client = Client()

# Define the function for generating creative writing prompts
def generate_writing_prompt(user_input):
    response = client.chat.completions.create(
        model="claude-3.5-sonnet",
        messages=[{"role": "user", "content": user_input}],
    )
    return response.choices[0].message.content

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    user_input = request.json.get('user_input')
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    try:
        result = generate_writing_prompt(user_input)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)