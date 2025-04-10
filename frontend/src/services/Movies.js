import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const searchMovies = async (query, limit = 10) => {
    try {
        const response = await api.get(`/movies/search?query=${encodeURIComponent(query)}&limit=${limit}`);
        return response.data;
    } catch (error) {
        console.error('Error searching movies:', error);
        throw error;
    }
};

export const queryInformation = async (query) => {
    try {
        const response = await api.post('/movies/query', { query });
        console.log("response -------------------- ", response)
        return response.data;
    } catch (error) {
        console.error('Error querying information:', error);
        throw error;
    }
};


export const getRecommendations = async (preferences) => {
    try {
        const response = await api.post('/movies/recommend', {
            preferences,
            exclude_watched: false
        });
        return response.data;
    } catch (error) {
        console.error('Error getting recommendations:', error);
        throw error;
    }
};


export const compareMovies = async (titles) => {
    try {
        const response = await api.post('/movies/compare', { titles });
        return response.data;
    } catch (error) {
        console.error('Error comparing movies:', error);
        throw error;
    }
};
