from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import jwt
import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Data structures for storing data (in a real app, you would use a database)
# Using DSA concepts for data storage and retrieval
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.size = 0
    
    def add(self, key, value):
        new_node = Node(key, value)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.size += 1
        return new_node
    
    def get(self, key):
        current = self.head
        while current:
            if current.key == key:
                return current.value
            current = current.next
        return None
    
    def remove(self, key):
        if not self.head:
            return False
        
        if self.head.key == key:
            self.head = self.head.next
            self.size -= 1
            return True
        
        current = self.head
        while current.next and current.next.key != key:
            current = current.next
        
        if current.next:
            current.next = current.next.next
            self.size -= 1
            return True
        
        return False
    
    def get_all(self):
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result
    
    def update(self, key, value):
        current = self.head
        while current:
            if current.key == key:
                current.value = value
                return True
            current = current.next
        return False

class HashTable:
    def __init__(self, size=100):
        self.size = size
        self.table = [LinkedList() for _ in range(size)]
    
    def _hash(self, key):
        if isinstance(key, str):
            return sum(ord(c) for c in key) % self.size
        return key % self.size
    
    def insert(self, key, value):
        index = self._hash(key)
        existing = self.table[index].get(key)
        if existing:
            self.table[index].update(key, value)
            return value
        else:
            node = self.table[index].add(key, value)
            return node.value
    
    def get(self, key):
        index = self._hash(key)
        return self.table[index].get(key)
    
    def remove(self, key):
        index = self._hash(key)
        return self.table[index].remove(key)
    
    def get_all(self):
        result = []
        for linked_list in self.table:
            result.extend(linked_list.get_all())
        return result

# Initialize data structures
users = HashTable()
messages = HashTable()
friend_requests = HashTable()
friends = HashTable()
notifications = HashTable()
online_users = {}  # Maps user_id to socket_id
typing_users = {}  # Maps user_id to {target_id: timestamp}
message_status = HashTable()  # Stores message read status

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users.get(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    # Check if user already exists
    all_users = users.get_all()
    for user in all_users:
        if user['email'] == data['email']:
            return jsonify({'message': 'User already exists!'}), 409
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = generate_password_hash(data['password'], method='sha256')
    
    new_user = {
        'id': user_id,
        'username': data['username'],
        'email': data['email'],
        'password': hashed_password,
        'profilePic': '',
        'created_at': datetime.datetime.now().isoformat()
    }
    
    users.insert(user_id, new_user)
    
    # Generate token
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user': {
            'id': user_id,
            'username': new_user['username'],
            'email': new_user['email'],
            'profilePic': new_user['profilePic']
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password!'}), 400
    
    # Find user by email
    all_users = users.get_all()
    user = None
    for u in all_users:
        if u['email'] == data['email']:
            user = u
            break
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    # Generate token
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'profilePic': user['profilePic']
        }
    }), 200

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({
        'id': current_user['id'],
        'username': current_user['username'],
        'email': current_user['email'],
        'profilePic': current_user['profilePic']
    }), 200

@app.route('/api/auth/change-password', methods=['PUT'])
@token_required
def change_password(current_user):
    data = request.get_json()
    
    if not data or not data.get('currentPassword') or not data.get('newPassword'):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    # Verify current password
    if not check_password_hash(current_user['password'], data['currentPassword']):
        return jsonify({'message': 'Current password is incorrect!'}), 401
    
    # Update password
    current_user['password'] = generate_password_hash(data['newPassword'], method='sha256')
    users.insert(current_user['id'], current_user)
    
    return jsonify({'message': 'Password changed successfully!'}), 200

@app.route('/api/auth/delete-account', methods=['POST'])
@token_required
def delete_account(current_user):
    data = request.get_json()
    
    if not data or not data.get('password'):
        return jsonify({'message': 'Password is required!'}), 400
    
    # Verify password
    if not check_password_hash(current_user['password'], data['password']):
        return jsonify({'message': 'Password is incorrect!'}), 401
    
    # Delete all user data
    user_id = current_user['id']
    
    # Remove user from friends lists
    all_friendships = friends.get_all()
    for friendship in all_friendships:
        if friendship['user1Id'] == user_id or friendship['user2Id'] == user_id:
            friendship_id = friendship['id']
            friends.remove(friendship_id)
    
    # Remove friend requests
    all_requests = friend_requests.get_all()
    for request in all_requests:
        if request['senderId'] == user_id or request['receiverId'] == user_id:
            friend_requests.remove(request['id'])
    
    # Remove messages
    all_messages = messages.get_all()
    for message in all_messages:
        if message['senderId'] == user_id or message['receiverId'] == user_id:
            messages.remove(message['id'])
            message_status.remove(message['id'])
    
    # Remove notifications
    all_notifications = notifications.get_all()
    for notification in all_notifications:
        if notification.get('receiverId') == user_id:
            notifications.remove(notification['id'])
    
    # Remove user from online users
    if user_id in online_users:
        del online_users[user_id]
    
    # Finally, remove the user
    users.remove(user_id)
    
    return jsonify({'message': 'Account deleted successfully!'}), 200

@app.route('/api/users/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    
    if 'username' in data:
        current_user['username'] = data['username']
    
    if 'profilePic' in data:
        current_user['profilePic'] = data['profilePic']
    
    users.insert(current_user['id'], current_user)
    
    return jsonify({
        'id': current_user['id'],
        'username': current_user['username'],
        'email': current_user['email'],
        'profilePic': current_user['profilePic']
    }), 200

@app.route('/api/users/search', methods=['GET'])
@token_required
def search_users(current_user):
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify([]), 200
    
    # Search users
    all_users = users.get_all()
    results = []
    
    for user in all_users:
        if user['id'] != current_user['id'] and query in user['username'].lower():
            results.append({
                'id': user['id'],
                'username': user['username'],
                'profilePic': user['profilePic'],
                'status': 'online' if user['id'] in online_users else 'offline'
            })
    
    return jsonify(results), 200

@app.route('/api/friends/request', methods=['POST'])
@token_required
def send_friend_request(current_user):
    data = request.get_json()
    
    if not data or not data.get('receiverId'):
        return jsonify({'message': 'Missing receiver ID!'}), 400
    
    receiver_id = data['receiverId']
    receiver = users.get(receiver_id)
    
    if not receiver:
        return jsonify({'message': 'Receiver not found!'}), 404
    
    # Check if request already exists
    request_id = f"{current_user['id']}_{receiver_id}"
    existing_request = friend_requests.get(request_id)
    
    if existing_request:
        return jsonify({'message': 'Friend request already sent!'}), 409
    
    # Check if they are already friends
    friendship_id = f"{current_user['id']}_{receiver_id}"
    friendship_id_reverse = f"{receiver_id}_{current_user['id']}"
    
    if friends.get(friendship_id) or friends.get(friendship_id_reverse):
        return jsonify({'message': 'Already friends!'}), 409
    
    # Create friend request
    new_request = {
        'id': request_id,
        'senderId': current_user['id'],
        'receiverId': receiver_id,
        'status': 'pending',
        'created_at': datetime.datetime.now().isoformat()
    }
    
    friend_requests.insert(request_id, new_request)
    
    # Create notification for receiver
    notification_id = str(uuid.uuid4())
    new_notification = {
        'id': notification_id,
        'type': 'friend_request',
        'senderId': current_user['id'],
        'senderName': current_user['username'],
        'receiverId': receiver_id,
        'content': f"{current_user['username']} sent you a friend request",
        'read': False,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    notifications.insert(notification_id, new_notification)
    
    # Emit socket event if receiver is online
    if receiver_id in online_users:
        socketio.emit('friend_request', {
            'id': current_user['id'],
            'username': current_user['username'],
            'profilePic': current_user['profilePic'],
            'status': 'online'
        }, room=online_users[receiver_id])
        
        socketio.emit('notification', new_notification, room=online_users[receiver_id])
    
    return jsonify({'message': 'Friend request sent successfully!'}), 201

@app.route('/api/friends/accept/<user_id>', methods=['POST'])
@token_required
def accept_friend_request(current_user, user_id):
    # Check if request exists
    request_id = f"{user_id}_{current_user['id']}"
    friend_request = friend_requests.get(request_id)
    
    if not friend_request:
        return jsonify({'message': 'Friend request not found!'}), 404
    
    # Get sender user
    sender = users.get(user_id)
    
    if not sender:
        return jsonify({'message': 'User not found!'}), 404
    
    # Create friendship
    friendship_id = f"{current_user['id']}_{user_id}"
    new_friendship = {
        'id': friendship_id,
        'user1Id': current_user['id'],
        'user2Id': user_id,
        'created_at': datetime.datetime.now().isoformat()
    }
    
    friends.insert(friendship_id, new_friendship)
    
    # Remove friend request
    friend_requests.remove(request_id)
    
    # Create notifications for both users
    # For current user
    notification_id1 = str(uuid.uuid4())
    new_notification1 = {
        'id': notification_id1,
        'type': 'system',
        'receiverId': current_user['id'],
        'content': f"You are now friends with {sender['username']}",
        'read': False,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    notifications.insert(notification_id1, new_notification1)
    
    # For sender
    notification_id2 = str(uuid.uuid4())
    new_notification2 = {
        'id': notification_id2,
        'type': 'system',
        'receiverId': user_id,
        'content': f"{current_user['username']} accepted your friend request",
        'read': False,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    notifications.insert(notification_id2, new_notification2)
    
    # Emit socket events
    if user_id in online_users:
        socketio.emit('notification', new_notification2, room=online_users[user_id])
    
    # Return the friend object
    friend_data = {
        'id': user_id,
        'username': sender['username'],
        'profilePic': sender['profilePic'],
        'status': 'online' if user_id in online_users else 'offline'
    }
    
    return jsonify(friend_data), 200

@app.route('/api/friends/reject/<user_id>', methods=['POST'])
@token_required
def reject_friend_request(current_user, user_id):
    # Check if request exists
    request_id = f"{user_id}_{current_user['id']}"
    friend_request = friend_requests.get(request_id)
    
    if not friend_request:
        return jsonify({'message': 'Friend request not found!'}), 404
    
    # Remove friend request
    friend_requests.remove(request_id)
    
    return jsonify({'message': 'Friend request rejected successfully!'}), 200

@app.route('/api/friends', methods=['GET'])
@token_required
def get_friends(current_user):
    all_friendships = friends.get_all()
    user_friends = []
    
    for friendship in all_friendships:
        if friendship['user1Id'] == current_user['id'] or friendship['user2Id'] == current_user['id']:
            friend_id = friendship['user2Id'] if friendship['user1Id'] == current_user['id'] else friendship['user1Id']
            friend = users.get(friend_id)
            
            if friend:
                user_friends.append({
                    'id': friend['id'],
                    'username': friend['username'],
                    'profilePic': friend['profilePic'],
                    'status': 'online' if friend['id'] in online_users else 'offline'
                })
    
    return jsonify(user_friends), 200

@app.route('/api/friends/requests', methods=['GET'])
@token_required
def get_friend_requests(current_user):
    all_requests = friend_requests.get_all()
    pending_requests = []
    
    for req in all_requests:
        if req['receiverId'] == current_user['id'] and req['status'] == 'pending':
            sender = users.get(req['senderId'])
            
            if sender:
                pending_requests.append({
                    'id': sender['id'],
                    'username': sender['username'],
                    'profilePic': sender['profilePic'],
                    'status': 'online' if sender['id'] in online_users else 'offline'
                })
    
    return jsonify(pending_requests), 200

@app.route('/api/friends/<user_id>', methods=['DELETE'])
@token_required
def remove_friend(current_user, user_id):
    # Check if friendship exists
    friendship_id = f"{current_user['id']}_{user_id}"
    friendship_id_reverse = f"{user_id}_{current_user['id']}"
    
    friendship = friends.get(friendship_id)
    if not friendship:
        friendship = friends.get(friendship_id_reverse)
    
    if not friendship:
        return jsonify({'message': 'Friendship not found!'}), 404
    
    # Remove friendship
    if friendship_id == friendship['id']:
        friends.remove(friendship_id)
    else:
        friends.remove(friendship_id_reverse)
    
    return jsonify({'message': 'Friend removed successfully!'}), 200

@app.route('/api/messages', methods=['POST'])
@token_required
def send_message(current_user):
    data = request.get_json()
    
    if not data or not data.get('receiverId') or not data.get('content'):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    receiver_id = data['receiverId']
    receiver = users.get(receiver_id)
    
    if not receiver:
        return jsonify({'message': 'Receiver not found!'}), 404
    
    # Check if they are friends
    friendship_id = f"{current_user['id']}_{receiver_id}"
    friendship_id_reverse = f"{receiver_id}_{current_user['id']}"
    
    if not friends.get(friendship_id) and not friends.get(friendship_id_reverse):
        return jsonify({'message': 'You are not friends with this user!'}), 403
    
    # Create message
    message_id = str(uuid.uuid4())
    new_message = {
        'id': message_id,
        'senderId': current_user['id'],
        'receiverId': receiver_id,
        'content': data['content'],
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    messages.insert(message_id, new_message)
    
    # Create message status
    status_id = message_id
    message_status.insert(status_id, {
        'id': status_id,
        'messageId': message_id,
        'seen': False,
        'seenAt': None
    })
    
    # Create notification for receiver
    notification_id = str(uuid.uuid4())
    new_notification = {
        'id': notification_id,
        'type': 'message',
        'senderId': current_user['id'],
        'senderName': current_user['username'],
        'receiverId': receiver_id,
        'content': f"New message from {current_user['username']}",
        'read': False,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    notifications.insert(notification_id, new_notification)
    
    # Emit socket event if receiver is online
    if receiver_id in online_users:
        socketio.emit('message', new_message, room=online_users[receiver_id])
        socketio.emit('notification', new_notification, room=online_users[receiver_id])
    
    return jsonify(new_message), 201

@app.route('/api/messages/<friend_id>', methods=['GET'])
@token_required
def get_messages(current_user, friend_id):
    # Check if they are friends
    friendship_id = f"{current_user['id']}_{friend_id}"
    friendship_id_reverse = f"{friend_id}_{current_user['id']}"
    
    if not friends.get(friendship_id) and not friends.get(friendship_id_reverse):
        return jsonify({'message': 'You are not friends with this user!'}), 403
    
    # Get messages
    all_messages = messages.get_all()
    conversation = []
    
    for message in all_messages:
        if (message['senderId'] == current_user['id'] and message['receiverId'] == friend_id) or \
           (message['senderId'] == friend_id and message['receiverId'] == current_user['id']):
            # Get message status
            status = message_status.get(message['id'])
            message_with_status = {**message}
            
            if status:
                message_with_status['seen'] = status['seen']
                message_with_status['seenAt'] = status['seenAt']
            else:
                message_with_status['seen'] = False
                message_with_status['seenAt'] = None
            
            conversation.append(message_with_status)
            
            # Mark messages as seen if they are from friend
            if message['senderId'] == friend_id and not (status and status['seen']):
                status_id = message['id']
                message_status.insert(status_id, {
                    'id': status_id,
                    'messageId': message['id'],
                    'seen': True,
                    'seenAt': datetime.datetime.now().isoformat()
                })
                
                # Notify sender that message was seen
                if friend_id in online_users:
                    socketio.emit('message_seen', {
                        'messageId': message['id'],
                        'seenAt': datetime.datetime.now().isoformat()
                    }, room=online_users[friend_id])
    
    # Sort by timestamp
    conversation.sort(key=lambda x: x['timestamp'])
    
    return jsonify(conversation), 200

@app.route('/api/messages/<message_id>', methods=['DELETE'])
@token_required
def delete_message(current_user, message_id):
    message = messages.get(message_id)
    
    if not message:
        return jsonify({'message': 'Message not found!'}), 404
    
    if message['senderId'] != current_user['id']:
        return jsonify({'message': 'You can only delete your own messages!'}), 403
    
    messages.remove(message_id)
    
    # Also remove message status
    message_status.remove(message_id)
    
    return jsonify({'message': 'Message deleted successfully!'}), 200

@app.route('/api/messages/seen/<message_id>', methods=['PUT'])
@token_required
def mark_message_as_seen(current_user, message_id):
    message = messages.get(message_id)
    
    if not message:
        return jsonify({'message': 'Message not found!'}), 404
    
    if message['receiverId'] != current_user['id']:
        return jsonify({'message': 'You can only mark messages sent to you as seen!'}), 403
    
    # Update message status
    status_id = message_id
    message_status.insert(status_id, {
        'id': status_id,
        'messageId': message_id,
        'seen': True,
        'seenAt': datetime.datetime.now().isoformat()
    })
    
    # Notify sender that message was seen
    if message['senderId'] in online_users:
        socketio.emit('message_seen', {
            'messageId': message_id,
            'seenAt': datetime.datetime.now().isoformat()
        }, room=online_users[message['senderId']])
    
    return jsonify({'message': 'Message marked as seen!'}), 200

@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    all_notifications = notifications.get_all()
    user_notifications = []
    
    for notification in all_notifications:
        if notification.get('receiverId') == current_user['id']:
            user_notifications.append(notification)
    
    # Sort by timestamp (newest first)
    user_notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify(user_notifications), 200

@app.route('/api/notifications/<notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_as_read(current_user, notification_id):
    notification = notifications.get(notification_id)
    
    if not notification:
        return jsonify({'message': 'Notification not found!'}), 404
    
    if notification['receiverId'] != current_user['id']:
        return jsonify({'message': 'You can only mark your own notifications as read!'}), 403
    
    notification['read'] = True
    notifications.insert(notification_id, notification)
    
    return jsonify({'message': 'Notification marked as read!'}), 200

@app.route('/api/notifications/read-all', methods=['PUT'])
@token_required
def mark_all_notifications_as_read(current_user):
    all_notifications = notifications.get_all()
    
    for notification in all_notifications:
        if notification.get('receiverId') == current_user['id']:
            notification['read'] = True
            notifications.insert(notification['id'], notification)
    
    return jsonify({'message': 'All notifications marked as read!'}), 200

@app.route('/api/notifications/<notification_id>', methods=['DELETE'])
@token_required
def delete_notification(current_user, notification_id):
    notification = notifications.get(notification_id)
    
    if not notification:
        return jsonify({'message': 'Notification not found!'}), 404
    
    if notification['receiverId'] != current_user['id']:
        return jsonify({'message': 'You can only delete your own notifications!'}), 403
    
    notifications.remove(notification_id)
    
    return jsonify({'message': 'Notification deleted successfully!'}), 200

@app.route('/api/notifications/clear-all', methods=['DELETE'])
@token_required
def clear_all_notifications(current_user):
    all_notifications = notifications.get_all()
    
    for notification in all_notifications:
        if notification.get('receiverId') == current_user['id']:
            notifications.remove(notification['id'])
    
    return jsonify({'message': 'All notifications cleared!'}), 200

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('userId')
    if user_id:
        online_users[user_id] = request.sid
        
        # Notify friends that user is online
        all_friendships = friends.get_all()
        for friendship in all_friendships:
            if friendship['user1Id'] == user_id:
                friend_id = friendship['user2Id']
                if friend_id in online_users:
                    socketio.emit('friend_status', {'userId': user_id, 'status': 'online'}, room=online_users[friend_id])
            elif friendship['user2Id'] == user_id:
                friend_id = friendship['user1Id']
                if friend_id in online_users:
                    socketio.emit('friend_status', {'userId': user_id, 'status': 'online'}, room=online_users[friend_id])

@socketio.on('disconnect')
def handle_disconnect():
    for user_id, sid in list(online_users.items()):
        if sid == request.sid:
            del online_users[user_id]
            
            # Notify friends that user is offline
            all_friendships = friends.get_all()
            for friendship in all_friendships:
                if friendship['user1Id'] == user_id:
                    friend_id = friendship['user2Id']
                    if friend_id in online_users:
                        socketio.emit('friend_status', {'userId': user_id, 'status': 'offline'}, room=online_users[friend_id])
                elif friendship['user2Id'] == user_id:
                    friend_id = friendship['user1Id']
                    if friend_id in online_users:
                        socketio.emit('friend_status', {'userId': user_id, 'status': 'offline'}, room=online_users[friend_id])
            break

@socketio.on('send_message')
def handle_send_message(message):
    if message['receiverId'] in online_users:
        emit('message', message, room=online_users[message['receiverId']])

@socketio.on('typing')
def handle_typing(data):
    user_id = data.get('userId')
    target_id = data.get('targetId')
    
    if not user_id or not target_id:
        return
    if not user_id or not target_id:
        return
    
    # Update typing status
    if user_id not in typing_users:
        typing_users[user_id] = {}
    
    typing_users[user_id][target_id] = datetime.datetime.now().timestamp()
    
    # Notify target user
    if target_id in online_users:
        socketio.emit('user_typing', {
            'userId': user_id,
            'isTyping': True
        }, room=online_users[target_id])

@socketio.on('stop_typing')
def handle_stop_typing(data):
    user_id = data.get('userId')
    target_id = data.get('targetId')
    
    if not user_id or not target_id:
        return
    
    # Update typing status
    if user_id in typing_users and target_id in typing_users[user_id]:
        del typing_users[user_id][target_id]
    
    # Notify target user
    if target_id in online_users:
        socketio.emit('user_typing', {
            'userId': user_id,
            'isTyping': False
        }, room=online_users[target_id])
@app.route('/')
def index():
    return jsonify({'message': 'backend is running!'})
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
