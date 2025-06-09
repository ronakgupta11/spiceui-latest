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

export const modifyCode = async (imageData: string, prompt: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/modify`, {
      image: imageData,
      prompt
    });
    return response.data;
  } catch (error) {
    throw new Error('Failed to modify code');
  }
}; 