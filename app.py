from flask import Flask, request, jsonify, Response
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configuration
NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY', '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')
NVIDIA_BASE_URL = 'https://integrate.api.nvidia.com/v1'
DEFAULT_MODEL = "meta/llama-3.1-405b-instruct"

@app.route('/')
def home():
    return jsonify({
        "message": "NVIDIA NIM Proxy is running!",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health"
        }
    })

@app.route('/v1/chat/completions', methods=['POST', 'OPTIONS'])
def chat_completions():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        messages = data.get('messages', [])
        model = data.get('model', DEFAULT_MODEL)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1024)
        stream = data.get('stream', False)
        
        nim_payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if 'top_p' in data:
            nim_payload['top_p'] = data['top_p']
        if 'frequency_penalty' in data:
            nim_payload['frequency_penalty'] = data['frequency_penalty']
        if 'presence_penalty' in data:
            nim_payload['presence_penalty'] = data['presence_penalty']
        
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        nim_response = requests.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            json=nim_payload,
            headers=headers,
            stream=stream,
            timeout=60
        )
        
        if stream:
            def generate():
                for line in nim_response.iter_lines():
                    if line:
                        yield line + b'\n'
            
            return Response(generate(), mimetype='text/event-stream')
        else:
            return jsonify(nim_response.json()), nim_response.status_code
            
    except Exception as e:
        return jsonify({
            "error": {
                "message": str(e),
                "type": "proxy_error",
                "code": "internal_error"
            }
        }), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    try:
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        nim_response = requests.get(
            f"{NVIDIA_BASE_URL}/models",
            headers=headers,
            timeout=30
        )
        
        if nim_response.status_code == 200:
            return jsonify(nim_response.json()), 200
        else:
            return jsonify({
                "object": "list",
                "data": [
                    {
                        "id": "meta/llama-3.1-405b-instruct",
                        "object": "model",
                        "created": int(datetime.now().timestamp()),
                        "owned_by": "nvidia"
                    }
                ]
            }), 200
            
    except Exception as e:
        return jsonify({
            "object": "list",
            "data": [
                {
                    "id": DEFAULT_MODEL,
                    "object": "model",
                    "created": int(datetime.now().timestamp()),
                    "owned_by": "nvidia"
                }
            ]
        }), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "nvidia_key_set": bool(NVIDIA_API_KEY)}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
```

4. Click **"Commit changes"**

## Step 4: Add requirements.txt
1. Click **"Add file"** → **"Create new file"**
2. Name it: `requirements.txt`
3. Paste:
```
flask
requests
gunicorn
