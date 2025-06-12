import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const generateCode = async (imageData: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/generate`, {
      image: imageData
    });
    return response.data;
  } catch (error) {
    throw new Error('Failed to generate code');
  }
};

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface CodeModificationResponse {
  modified_files: { [key: string]: string };
  changes: Array<{ [key: string]: any }>;
  warnings: string[];
  explanation: string;
}

export const modifyCode = async (
  chatHistory: ChatMessage[], 
  currentCode: { [key: string]: string },
  available_components: Array<{ [key: string]: any }>
) => {
  try {
    console.log('Frontend modifyCode - Request payload:', {
      chat_history: chatHistory,
      current_code: currentCode,
      available_components
    });

    const response = await axios.post(`${API_BASE_URL}/modify`, {
      chat_history: chatHistory.map(msg => ({
        content: msg.content,
        role: msg.role,
        timestamp: msg.timestamp.toISOString()
      })),
      current_code: currentCode,
      available_components
    });

    console.log('Frontend modifyCode - Response:', response.data);
    return response.data as CodeModificationResponse;
  } catch (error) {
    console.error('Frontend modifyCode - Error:', error);
    if (axios.isAxiosError(error) && error.response) {
      console.error('Error response data:', error.response.data);
    }
    throw new Error('Failed to modify code');
  }
}; 