import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Configuring axios for API calls
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Movie services for API calls
export const searchMovies = async (query, limit = 10) => {
    const response = await api.get(`/movies/search?query=${encodeURIComponent(query)}&limit=${limit}`);
    return response.data;
};

export const queryInformation = async (query) => {
    const response = await api.post('/movies/query', { query });
    return response.data;
};

export const getRecommendations = async (preferences) => {
    const response = await api.post('/movies/recommend', {
        preferences,
        exclude_watched: false
    });
    return response.data;
};

export const compareMovies = async (titles) => {
    const response = await api.post('/movies/compare', { titles });
    return response.data;
};

export default api;