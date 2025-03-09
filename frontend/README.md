# Real-Time Chat Application

A full-stack real-time chat application with React.js frontend and Python Flask backend using data structures and algorithms.

## Features

- User authentication (login/register)
- Real-time messaging
- Friend requests and management
- Notifications system
- Profile management
- Online/offline status

## Tech Stack

### Frontend
- React.js
- TypeScript
- Tailwind CSS
- Socket.io client
- Axios for API requests
- React Router for navigation
- Lucide React for icons

### Backend
- Python Flask
- Custom DSA implementations (LinkedList, HashTable)
- Flask-SocketIO for real-time communication
- JWT for authentication

## Getting Started

### Prerequisites
- Node.js
- Python 3.x

### Running the Frontend

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

### Running the Backend

```bash
# Navigate to the backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the Flask server
python app.py
```

## Project Structure

### Frontend
- `src/contexts/` - React context providers for auth, chat, and notifications
- `src/pages/` - Main application pages (Login, Register, ChatRoom, Profile)
- `src/components/` - Reusable UI components

### Backend
- `app.py` - Main Flask application with routes and socket handlers
- Custom data structures for storing user data, messages, and more

## Data Structures Used

The backend implements custom data structures:
- **LinkedList**: For sequential data storage
- **HashTable**: For efficient key-value lookups
- These structures are used to store users, messages, friend requests, etc.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login a user
- `GET /api/auth/me` - Get current user info

### Users
- `PUT /api/users/profile` - Update user profile
- `GET /api/users/search` - Search for users

### Friends
- `POST /api/friends/request` - Send a friend request
- `POST /api/friends/accept/:userId` - Accept a friend request
- `POST /api/friends/reject/:userId` - Reject a friend request
- `GET /api/friends` - Get all friends
- `GET /api/friends/requests` - Get pending friend requests
- `DELETE /api/friends/:userId` - Remove a friend

### Messages
- `POST /api/messages` - Send a message
- `GET /api/messages/:friendId` - Get conversation with a friend
- `DELETE /api/messages/:messageId` - Delete a message

### Notifications
- `GET /api/notifications` - Get all notifications
- `PUT /api/notifications/:notificationId/read` - Mark notification as read
- `PUT /api/notifications/read-all` - Mark all notifications as read
- `DELETE /api/notifications/:notificationId` - Delete a notification
- `DELETE /api/notifications/clear-all` - Clear all notifications