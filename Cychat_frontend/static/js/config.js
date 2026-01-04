/**
 * Cy Chat Frontend Configuration
 * 
 * Update these values to match your backend server configuration.
 */

const CONFIG = {
    // API Base URL (REST endpoints)
    API_BASE: 'http://localhost:8000/api/v1',
    
    // WebSocket Base URL
    WS_BASE: 'ws://localhost:8000/api/v1',
    
    // Storage keys
    STORAGE_KEYS: {
        ACCESS_TOKEN: 'access_token',
        TOKEN_TYPE: 'token_type',
        USER_DATA: 'user_data'
    },
    
    // Default timeout for API requests (ms)
    REQUEST_TIMEOUT: 30000,
    
    // WebSocket reconnection settings
    WS_RECONNECT: {
        MAX_ATTEMPTS: 5,
        DELAY_MS: 3000
    }
};

/**
 * API Endpoints Reference
 * 
 * Authentication:
 *   POST /auth/login          - Login (OAuth2 password flow)
 *   POST /auth/register       - Register new user
 * 
 * User Profile:
 *   GET  /user/profile        - Get current user profile
 *   PUT  /user/profile        - Update profile info
 *   GET  /user/logout         - Logout (blacklist token)
 *   PUT  /user/reset-password - Reset password
 *   PUT  /user/profile-image  - Upload profile image
 *   GET  /user/profile-image/{name} - Get profile image
 * 
 * Contacts:
 *   POST   /contact           - Add contact
 *   GET    /contacts          - Get all contacts
 *   GET    /contacts/users/search - Search contacts
 *   DELETE /contact/delete    - Delete contact
 * 
 * Chats:
 *   POST   /message           - Send a message
 *   GET    /conversation      - Get conversation with user
 *   GET    /contacts/chat/search - Search chat contacts
 *   DELETE /user/chat         - Delete chat messages
 * 
 * Rooms:
 *   POST   /room              - Create/join room
 *   GET    /room/conversation - Get room messages
 *   POST   /room/message      - Send room message
 *   DELETE /room              - Leave room
 *   GET    /rooms             - Get user's rooms
 *   GET    /rooms/search      - Search rooms
 * 
 * WebSockets:
 *   WS /ws/{sender_id}/{room_name}       - Room chat
 *   WS /ws/chat/{sender_id}/{receiver_id} - Direct chat
 */

// Helper functions
const API = {
    /**
     * Get authentication token
     */
    getToken() {
        return localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    },

    /**
     * Get authorization headers
     */
    getAuthHeaders() {
        const token = this.getToken();
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    },

    /**
     * Logout and clear storage
     */
    logout() {
        localStorage.removeItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.TOKEN_TYPE);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
        window.location.href = 'login.html';
    },

    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE}${endpoint}`;
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                this.logout();
                throw new Error('Unauthorized');
            }

            return response;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, API };
}