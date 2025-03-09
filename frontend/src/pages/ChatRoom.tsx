import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { useNotifications } from '../contexts/NotificationContext';
import { 
  MessageCircle, 
  Users, 
  Bell, 
  LogOut, 
  User, 
  Send, 
  Search, 
  Trash2, 
  UserPlus, 
  X, 
  Check,
  CheckCheck
} from 'lucide-react';

const ChatRoom: React.FC = () => {
  const { user, logout } = useAuth();
  const { 
    friends, 
    friendRequests, 
    messages, 
    currentChat, 
    loadingFriends,
    loadingMessages,
    typingUsers,
    setCurrentChat, 
    sendMessage, 
    deleteMessage,
    sendFriendRequest,
    acceptFriendRequest,
    rejectFriendRequest,
    removeFriend,
    searchUsers,
    setTyping
  } = useChat();
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead, 
    deleteNotification 
  } = useNotifications();
  
  const navigate = useNavigate();
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showFriendRequests, setShowFriendRequests] = useState(false);
  const [requestStatus, setRequestStatus] = useState<{ message: string; isError: boolean } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentChat, messages]);
  
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!messageInput.trim() || !currentChat) return;
    
    try {
      await sendMessage(messageInput);
      setMessageInput('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };
  
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const results = await searchUsers(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };
  
  const handleSendFriendRequest = async (userId: string) => {
    try {
      const result = await sendFriendRequest(userId);
      if (result.success) {
        setRequestStatus({ message: result.message, isError: false });
      } else {
        setRequestStatus({ message: result.message, isError: true });
      }
      
      // Clear status message after 3 seconds
      setTimeout(() => {
        setRequestStatus(null);
      }, 3000);
    } catch (error) {
      console.error('Error sending friend request:', error);
    }
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessageInput(e.target.value);
    
    // Trigger typing indicator
    if (e.target.value.trim() !== '') {
      setTyping(true);
    } else {
      setTyping(false);
    }
  };
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  const handleProfileClick = () => {
    navigate('/profile');
  };
  
  const currentMessages = currentChat ? messages[currentChat.id] || [] : [];
  const isTyping = currentChat ? typingUsers[currentChat.id] : false;
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* User info */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
              {user?.username.charAt(0).toUpperCase()}
            </div>
            <div className="ml-3">
              <p className="font-medium text-gray-800">{user?.username}</p>
              <p className="text-xs text-gray-500">Online</p>
            </div>
          </div>
          <div className="flex">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-gray-500 hover:text-blue-500 focus:outline-none"
            >
              <Bell size={20} />
              {unreadCount > 0 && (
                <span className="absolute top-0 right-0 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>
            <button 
              onClick={handleProfileClick}
              className="p-2 text-gray-500 hover:text-blue-500 focus:outline-none"
            >
              <User size={20} />
            </button>
            <button 
              onClick={handleLogout}
              className="p-2 text-gray-500 hover:text-blue-500 focus:outline-none"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
        
        {/* Search */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search users..."
              className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Search 
              size={18} 
              className="absolute left-3 top-2.5 text-gray-400" 
            />
            <button
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
              className="absolute right-2 top-1.5 px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 focus:outline-none disabled:opacity-50"
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>
          
          {/* Request status message */}
          {requestStatus && (
            <div className={`mt-2 p-2 text-sm rounded ${
              requestStatus.isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
            }`}>
              {requestStatus.message}
            </div>
          )}
          
          {/* Search results */}
          {searchResults.length > 0 && (
            <div className="mt-2 border border-gray-200 rounded-md overflow-hidden">
              <div className="bg-gray-50 px-3 py-2 text-xs font-medium text-gray-500">
                Search Results
              </div>
              <div className="max-h-40 overflow-y-auto">
                {searchResults.map((result) => (
                  <div 
                    key={result.id} 
                    className="px-3 py-2 border-t border-gray-200 flex items-center justify-between"
                  >
                    <div className="flex items-center">
                      <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center text-white font-semibold">
                        {result.username.charAt(0).toUpperCase()}
                      </div>
                      <span className="ml-2 text-sm font-medium">{result.username}</span>
                    </div>
                    <button
                      onClick={() => handleSendFriendRequest(result.id)}
                      className="p-1 text-blue-500 hover:text-blue-700 focus:outline-none"
                    >
                      <UserPlus size={16} />
                    </button>
                  </div>
                ))}
              </div>
              <button
                onClick={() => setSearchResults([])}
                className="w-full px-3 py-1 bg-gray-50 text-xs text-gray-500 hover:bg-gray-100 focus:outline-none"
              >
                Close
              </button>
            </div>
          )}
        </div>
        
        {/* Friend requests */}
        {friendRequests.length > 0 && (
          <div className="px-4 py-2 border-b border-gray-200">
            <button
              onClick={() => setShowFriendRequests(!showFriendRequests)}
              className="w-full flex items-center justify-between text-sm font-medium text-blue-500 hover:text-blue-700 focus:outline-none"
            >
              <span>Friend Requests ({friendRequests.length})</span>
              <span>{showFriendRequests ? '▲' : '▼'}</span>
            </button>
            
            {showFriendRequests && (
              <div className="mt-2 space-y-2">
                {friendRequests.map((request) => (
                  <div 
                    key={request.id} 
                    className="p-2 bg-gray-50 rounded-md flex items-center justify-between"
                  >
                    <div className="flex items-center">
                      <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center text-white font-semibold">
                        {request.username.charAt(0).toUpperCase()}
                      </div>
                      <span className="ml-2 text-sm font-medium">{request.username}</span>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => acceptFriendRequest(request.id)}
                        className="p-1 text-green-500 hover:text-green-700 focus:outline-none"
                        title="Accept"
                      >
                        <Check size={16} />
                      </button>
                      <button
                        onClick={() => rejectFriendRequest(request.id)}
                        className="p-1 text-red-500 hover:text-red-700 focus:outline-none"
                        title="Reject"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Friends list */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center">
            <Users size={16} className="text-gray-500 mr-2" />
            <h3 className="text-sm font-medium text-gray-500">Friends</h3>
          </div>
          
          {loadingFriends ? (
            <div className="flex justify-center items-center h-20">
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : friends.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">
              No friends yet. Search for users to add friends.
            </div>
          ) : (
            <div>
              {friends.map((friend) => (
                <div 
                  key={friend.id} 
                  onClick={() => setCurrentChat(friend)}
                  className={`px-4 py-3 flex items-center cursor-pointer hover:bg-gray-50 ${
                    currentChat?.id === friend.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="relative">
                    <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center text-white font-semibold">
                      {friend.username.charAt(0).toUpperCase()}
                    </div>
                    <div className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white ${
                      friend.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                    }`}></div>
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-gray-800">{friend.username}</p>
                    <p className="text-xs text-gray-500">
                      {friend.status === 'online' ? 'Online' : 'Offline'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {currentChat ? (
          <>
            {/* Chat header */}
            <div className="px-6 py-4 bg-white border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center">
                <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center text-white font-semibold">
                  {currentChat.username.charAt(0).toUpperCase()}
                </div>
                <div className="ml-3">
                  <p className="font-medium text-gray-800">{currentChat.username}</p>
                  <p className="text-xs text-gray-500">
                    {currentChat.status === 'online' ? 'Online' : 'Offline'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => removeFriend(currentChat.id)}
                className="text-gray-500 hover:text-red-500 focus:outline-none"
                title="Remove friend"
              >
                <X size={20} />
              </button>
            </div>
            
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
              {loadingMessages ? (
                <div className="flex justify-center items-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              ) : currentMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <MessageCircle size={48} className="mb-2 opacity-50" />
                  <p>No messages yet. Start the conversation!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {currentMessages.map((message) => {
                    const isOwnMessage = message.senderId === user?.id;
                    
                    return (
                      <div 
                        key={message.id} 
                        className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          isOwnMessage 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-white text-gray-800 border border-gray-200'
                        }`}>
                          <div className="flex items-end">
                            <p className="text-sm">{message.content}</p>
                            <div className="ml-2 flex items-center">
                              <span className="text-xs opacity-70">
                                {new Date(message.timestamp).toLocaleTimeString([], { 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })}
                              </span>
                              {isOwnMessage && (
                                <>
                                  {message.seen ? (
                                    <span className="ml-1 text-xs" title={message.seenAt ? `Seen at ${new Date(message.seenAt).toLocaleTimeString()}` : 'Seen'}>
                                      <CheckCheck size={12} className="text-white opacity-70" />
                                    </span>
                                  ) : (
                                    <span className="ml-1 text-xs">
                                      <Check size={12} className="text-white opacity-70" />
                                    </span>
                                  )}
                                  <button
                                    onClick={() => deleteMessage(message.id)}
                                    className="ml-1 opacity-70 hover:opacity-100 focus:outline-none"
                                  >
                                    <Trash2 size={12} />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-gray-200 px-4 py-2 rounded-lg">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                          <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                          <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
            
            {/* Message input */}
            <div className="px-4 py-3 bg-white border-t border-gray-200">
              <form onSubmit={handleSendMessage} className="flex items-center">
                <input
                  type="text"
                  value={messageInput}
                  onChange={handleInputChange}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={!messageInput.trim()}
                  className="px-4 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full bg-gray-50 text-gray-500">
            <MessageCircle size={64} className="mb-4 opacity-50" />
            <h3 className="text-xl font-medium mb-2">Welcome to Chat App</h3>
            <p className="text-center max-w-md">
              Select a friend from the list to start chatting or search for new friends.
            </p>
          </div>
        )}
      </div>
      
      {/* Notifications panel */}
      {showNotifications && (
        <div className="absolute top-0 right-0 h-screen w-80 bg-white shadow-lg border-l border-gray-200 z-10">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-medium text-gray-800">Notifications</h3>
            <div className="flex space-x-2">
              <button
                onClick={markAllAsRead}
                className="text-xs text-blue-500 hover:text-blue-700 focus:outline-none"
              >
                Mark all as read
              </button>
              <button
                onClick={() => setShowNotifications(false)}
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <X size={18} />
              </button>
            </div>
          </div>
          
          <div className="overflow-y-auto h-full pb-20">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No notifications
              </div>
            ) : (
              <div>
                {notifications.map((notification) => (
                  <div 
                    key={notification.id} 
                    className={`p-4 border-b border-gray-100 ${
                      !notification.read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex justify-between">
                      <p className="text-sm">
                        {notification.content}
                      </p>
                      <div className="flex items-start ml-2">
                        {!notification.read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="p-1 text-blue-500 hover:text-blue-700 focus:outline-none"
                            title="Mark as read"
                          >
                            <Check size={14} />
                          </button>
                        )}
                        <button
                          onClick={() => deleteNotification(notification.id)}
                          className="p-1 text-gray-500 hover:text-red-500 focus:outline-none"
                          title="Delete"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(notification.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatRoom;