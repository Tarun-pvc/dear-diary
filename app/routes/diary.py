from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from bson.objectid import ObjectId
from ..db import mongo
from datetime import datetime, timedelta
import calendar
from flask import current_app
from app.ai.rag import generate_response

diary_bp = Blueprint('diary', __name__, url_prefix='/diary')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_recent_entries(limit=5):
    """Helper function to get recent entries for sidebar"""
    entries = list(mongo.db.diaries.find(
        {'username': session.get('user'), 'is_deleted': {'$ne': True}}
    ).sort('updated_at', -1).limit(limit))
    
    # Convert ObjectId to string for each entry
    for entry in entries:
        entry['id'] = str(entry['_id'])
    
    return entries

@diary_bp.route('/')
@login_required
def index():
    """Main diary page - redirects to dashboard or today's entry."""
    # Redirect to the dashboard as the main entry point
    return redirect(url_for('diary.dashboard'))

@diary_bp.route('/dashboard')
@login_required
def dashboard():
    """Calendar view dashboard"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    recent_entries = get_recent_entries()
    current_entry = None  # Initialize as None for dashboard view
    
    return render_template('dashboard.html', 
                         entries=recent_entries,  # Pass as entries for consistency
                         recent_entries=recent_entries,
                         current_entry=current_entry,
                         user=session.get('user'))

@diary_bp.route('/all-entries')
@login_required
def all_entries():
    """All entries list view"""
    recent_entries = get_recent_entries()
    
    # Get all entries for the user without date filtering
    entries = list(mongo.db.diaries.find({
        'username': session.get('user'),
        'is_deleted': {'$ne': True}
    }).sort('created_at', -1))
    
    # Convert ObjectId to string for each entry
    for entry in entries:
        entry['id'] = str(entry['_id'])
    
    return render_template('all_entries.html',
                         entries=entries,
                         recent_entries=recent_entries,
                         view_type='all')

@diary_bp.route('/bookmarked')
@login_required
def bookmarked_entries():
    """Bookmarked entries view"""
    recent_entries = get_recent_entries()
    
    entries = list(mongo.db.diaries.find({
        'username': session.get('user'),
        'is_deleted': {'$ne': True},
        'is_bookmarked': True
    }).sort('created_at', -1))
    
    # Convert ObjectId to string for each entry
    for entry in entries:
        entry['id'] = str(entry['_id'])
    
    return render_template('all_entries.html',
                         entries=entries,
                         recent_entries=recent_entries,
                         view_type='bookmarked')

# Add alias route for bookmarks to fix the BuildError
@diary_bp.route('/bookmarks')
@login_required
def bookmarks():
    """Alias for bookmarked_entries"""
    return bookmarked_entries()

@diary_bp.route('/deleted')
@login_required
def deleted_entries():
    """Deleted entries view"""
    recent_entries = get_recent_entries()
    
    entries = list(mongo.db.diaries.find({
        'username': session.get('user'),
        'is_deleted': True
    }).sort('created_at', -1))
    
    # Convert ObjectId to string for each entry
    for entry in entries:
        entry['id'] = str(entry['_id'])
    
    return render_template('all_entries.html',
                         entries=entries,
                         recent_entries=recent_entries,
                         view_type='deleted')

@diary_bp.route('/entry/<entry_id>')
@login_required
def view_entry(entry_id):
    """Single entry detail view"""
    recent_entries = get_recent_entries()
    
    current_entry = mongo.db.diaries.find_one({
        '_id': ObjectId(entry_id),
        'username': session.get('user')
    })
    
    if not current_entry:
        flash('Entry not found', 'error')
        return redirect(url_for('diary.dashboard'))
    
    current_entry['id'] = str(current_entry['_id'])
    
    return render_template('entry_detail.html',
                         entry=current_entry,
                         current_entry=current_entry,
                         recent_entries=recent_entries)

@diary_bp.route('/calendar_data')
@login_required
def calendar_data():
    """Get calendar data for the specified month"""
    month = int(request.args.get('month', datetime.now().month))
    year = int(request.args.get('year', datetime.now().year))
    
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
    
    entries = list(mongo.db.diaries.find({
        'username': session.get('user'),
        'is_deleted': {'$ne': True},
        'created_at': {
            '$gte': first_day,
            '$lte': last_day
        }
    }))
    
    days_with_entries = set()
    for entry in entries:
        days_with_entries.add(entry['created_at'].day)
    
    # Calculate streak
    today = datetime.now()
    streak = 0
    current_date = today
    
    while True:
        day_entries = mongo.db.diaries.find_one({
            'username': session.get('user'),
            'is_deleted': {'$ne': True},
            'created_at': {
                '$gte': current_date.replace(hour=0, minute=0, second=0),
                '$lt': current_date.replace(hour=23, minute=59, second=59)
            }
        })
        
        if not day_entries:
            break
            
        streak += 1
        current_date -= timedelta(days=1)
    
    return jsonify({
        'days_with_entries': list(days_with_entries),
        'streak': streak
    })

@diary_bp.route('/entries_by_date')
@login_required
def entries_by_date():
    """Get entries for a specific date"""
    date_str = request.args.get('date')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        start_of_day = date.replace(hour=0, minute=0, second=0)
        end_of_day = date.replace(hour=23, minute=59, second=59)
        
        entries = list(mongo.db.diaries.find({
            'username': session.get('user'),
            'is_deleted': {'$ne': True},
            'created_at': {
                '$gte': start_of_day,
                '$lte': end_of_day
            }
        }).sort('created_at', -1))
        
        formatted_entries = []
        for entry in entries:
            formatted_entries.append({
                'id': str(entry['_id']),
                'title': entry.get('title', 'Untitled Entry'),
                'content': entry.get('content', '')[:100] + '...',
                'emoji': entry.get('emoji', '📝'),
                'created_at': entry['created_at'].strftime('%H:%M')
            })
        
        return jsonify({
            'entries': formatted_entries,
            'count': len(formatted_entries)
        })
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@diary_bp.route('/save_entry', methods=['POST'])
@login_required
def save_entry():
    """Save or update an entry"""
    data = request.get_json()
    entry_id = data.get('id')
    now = datetime.now()
    
    entry_data = {
        'title': data.get('title', 'Untitled Entry'),
        'content': data.get('content', ''),
        'emoji': data.get('emoji', '📝'),
        'mood_emoji': data.get('mood_emoji', '😊'),
        'wakeup_time': data.get('wakeup_time'),
        'sleep_time': data.get('sleep_time'),
        'learnings': data.get('learnings', ''),
        'updated_at': now
    }
    
    if entry_id:  # Update existing entry
        result = mongo.db.diaries.update_one(
            {'_id': ObjectId(entry_id), 'username': session.get('user')},
            {'$set': entry_data}
        )
        if result.modified_count == 0:
            return jsonify({'error': 'Entry not found or unauthorized'}), 404
    else:  # Create new entry
        entry_data.update({
            'username': session.get('user'),
            'created_at': now,
            'updated_at': now,  # Set initial updated_at same as created_at
            'is_deleted': False,
            'is_bookmarked': False
        })
        result = mongo.db.diaries.insert_one(entry_data)
        entry_id = str(result.inserted_id)
    
    return jsonify({
        'id': entry_id,
        'message': 'Entry saved successfully'
    })

@diary_bp.route('/toggle_bookmark/<entry_id>', methods=['POST'])
@login_required
def toggle_bookmark(entry_id):
    """Toggle bookmark status of an entry"""
    entry = mongo.db.diaries.find_one({
        '_id': ObjectId(entry_id),
        'username': session.get('user')
    })
    
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
    
    is_bookmarked = not entry.get('is_bookmarked', False)
    
    mongo.db.diaries.update_one(
        {'_id': ObjectId(entry_id)},
        {'$set': {'is_bookmarked': is_bookmarked}}
    )
    
    return jsonify({
        'is_bookmarked': is_bookmarked,
        'message': 'Bookmark updated successfully'
    })

@diary_bp.route('/delete_entry/<entry_id>', methods=['DELETE'])
@login_required
def delete_entry(entry_id):
    """Soft delete an entry"""
    result = mongo.db.diaries.update_one(
        {'_id': ObjectId(entry_id), 'username': session.get('user')},
        {'$set': {'is_deleted': True}}
    )
    
    if result.modified_count == 0:
        return jsonify({'error': 'Entry not found or unauthorized'}), 404
    
    return jsonify({'message': 'Entry deleted successfully'})

@diary_bp.route('/restore_entry/<entry_id>', methods=['POST'])
@login_required
def restore_entry(entry_id):
    """Restore a deleted entry"""
    result = mongo.db.diaries.update_one(
        {'_id': ObjectId(entry_id), 'username': session.get('user')},
        {'$set': {'is_deleted': False}}
    )
    
    if result.modified_count == 0:
        return jsonify({'error': 'Entry not found or unauthorized'}), 404
    
    return jsonify({'message': 'Entry restored successfully'})

@diary_bp.route('/buddy')
@login_required
def buddy_chat():
    """Buddy's Corner chat view"""
    recent_entries = get_recent_entries()
    return render_template('buddy_chat.html', recent_entries=recent_entries)

@diary_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages with Buddy using RAG for augmented generation"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Store user message
        mongo.db.chat_history.insert_one({
            'username': session.get('user'),
            'message': user_message,
            'type': 'user',
            'timestamp': datetime.now()
        })
        
        # Log start time for performance monitoring
        start_time = datetime.now()
        current_app.logger.info(f"Processing chat message: '{user_message}'")
        
        # Generate AI response using RAG
        ai_response = generate_response(user_message, mongo, session.get('user'))
        
        # Log completion time
        processing_time = (datetime.now() - start_time).total_seconds()
        current_app.logger.info(f"Generated response in {processing_time:.2f} seconds")
        
        # Store AI response
        mongo.db.chat_history.insert_one({
            'username': session.get('user'),
            'message': ai_response,
            'type': 'ai',
            'timestamp': datetime.now()
        })
        
        return jsonify({'response': ai_response})
    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'response': "I'm having trouble connecting to my memory. Please try again later."}), 500

@diary_bp.route('/update_entry/<entry_id>', methods=['PUT'])
@login_required
def update_entry(entry_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    now = datetime.now()
    
    entry = mongo.db.diaries.find_one({'_id': ObjectId(entry_id), 'username': session['user']})
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    update_data = {
        'title': data.get('title', entry.get('title', 'Untitled')),
        'content': data.get('content', entry.get('content', '')),
        'emoji': data.get('emoji', entry.get('emoji', '📝')),
        'updated_at': now
    }
    
    mongo.db.diaries.update_one(
        {'_id': ObjectId(entry_id)},
        {'$set': update_data}
    )
    
    return jsonify({'success': True}), 200

@diary_bp.route('/entry/<entry_id>/json')
@login_required
def get_entry_json(entry_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    entry = mongo.db.diaries.find_one({'_id': ObjectId(entry_id), 'username': session['user']})
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    entry['id'] = str(entry['_id'])
    del entry['_id']
    
    return jsonify(entry), 200

@diary_bp.route('/chat_history')
@login_required
def get_chat_history():
    """Get recent chat history for the current user"""
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
        current_app.logger.error(f"Error fetching chat history: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'history': []}), 500
