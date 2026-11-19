import axios from 'axios';

// Use direct API URL with CORS enabled
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8008';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generate a simple session ID
export const generateSessionId = () => {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
};

export default apiClient;
