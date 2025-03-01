from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from ..db import mongo
from datetime import datetime
from app.ai.rag import generate_response

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@chat_bp.route('/')
@login_required
def chat_interface():
    """Main chat interface"""
    return render_template('chat.html')

@chat_bp.route('/send', methods=['POST'])
@login_required
def chat_send():
    """Handle incoming chat messages"""
    message = request.form.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Store user message
        mongo.db.chat_history.insert_one({
            'username': session.get('user'),
            'message': message,
            'type': 'user',
            'timestamp': datetime.now()
        })
        
        # Generate AI response using RAG
        ai_response = generate_response(message, mongo, session.get('user'))
        
        # Store AI response
        mongo.db.chat_history.insert_one({
            'username': session.get('user'),
            'message': ai_response,
            'type': 'ai',
            'timestamp': datetime.now()
        })
        
        return jsonify({'response': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/history')
@login_required
def chat_history():
    """Get chat history for the current user"""
    try:
        # Get most recent 50 messages
        history = list(mongo.db.chat_history.find(
            {'username': session.get('user')}
        ).sort('timestamp', -1).limit(50))
        
        # Format for front-end
        formatted_history = []
        for msg in reversed(history):  # Reverse to get chronological order
            formatted_history.append({
                'message': msg.get('message', ''),
                'type': msg.get('type', 'ai'),
                'timestamp': msg.get('timestamp').isoformat() if msg.get('timestamp') else None
            })
            
        return jsonify({'history': formatted_history})
    except Exception as e:
        return jsonify({'error': str(e), 'history': []}), 500
