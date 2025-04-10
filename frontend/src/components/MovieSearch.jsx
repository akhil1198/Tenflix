import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { searchMovies } from '../services/Movies';
import { Film, Search as SearchIcon, Filter, Star } from 'lucide-react';

const MovieSearch = () => {
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);

    const [query, setQuery] = useState(queryParams.get('query') || '');
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState({
        type: 'all', // 'movie', 'tv', 'all'
        genre: '',
        year: '',
        sort: 'relevance' // 'relevance', 'year', 'rating'
    });

    const performSearch = async (searchQuery) => {
        if (!searchQuery.trim()) return;

        try {
            setIsLoading(true);
            setError('');

            const data = await searchMovies(searchQuery, 20);
            setResults(data.results || []);

        } catch (err) {
            setError('Error searching for movies. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle initial search from URL
    useEffect(() => {
        if (query) {
            performSearch(query);
        }
    }, []);

    const handleSearch = (e) => {
        e.preventDefault();
        performSearch(query);
    };

    const toggleFilters = () => {
        setShowFilters(!showFilters);
    };

    const handleFilterChange = (key, value) => {
        setFilters({
            ...filters,
            [key]: value
        });
    };

    // Applying filters to results
    const filteredResults = results.filter(item => {
        // Filter by type
        if (filters.type !== 'all' && item.media_type !== filters.type) {
            return false;
        }

        // Filter by genre
        if (filters.genre && (!item.genres || !item.genres.includes(filters.genre))) {
            return false;
        }

        // Filter by year
        if (filters.year && item.year !== filters.year) {
            return false;
        }

        return true;
    });

    // Sort results
    const sortedResults = [...filteredResults].sort((a, b) => {
        if (filters.sort === 'year') {
            return parseInt(b.year || 0) - parseInt(a.year || 0);
        } else if (filters.sort === 'rating') {
            return (b.rating || 0) - (a.rating || 0);
        }
        return 0;
    });

    return (
        <div className="py-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Movie & TV Show Search</h1>
                <p className="text-gray-600 mt-2">
                    Find information about your favorite movies and shows
                </p>
            </header>

            {/* Search Form */}
            <div className="bg-white rounded-lg shadow p-6 mb-8">
                <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
                    <div className="flex-grow relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <SearchIcon className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search for movies, TV shows, actors, directors..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div className="flex gap-2">
                        <button
                            type="submit"
                            className="bg-blue-600 text-white py-2 px-6 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={isLoading}
                        >
                            {isLoading ? 'Searching...' : 'Search'}
                        </button>

                        <button
                            type="button"
                            onClick={toggleFilters}
                            className="bg-gray-200 text-gray-700 py-2 px-4 rounded hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 flex items-center"
                        >
                            <Filter className="h-4 w-4 mr-1" />
                            Filters
                        </button>
                    </div>
                </form>

                {/* Filters Panel */}
                {showFilters && (
                    <div className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                            <select
                                value={filters.type}
                                onChange={(e) => handleFilterChange('type', e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">All</option>
                                <option value="movie">Movies</option>
                                <option value="tv">TV Shows</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Genre</label>
                            <select
                                value={filters.genre}
                                onChange={(e) => handleFilterChange('genre', e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">All Genres</option>
                                <option value="Action">Action</option>
                                <option value="Comedy">Comedy</option>
                                <option value="Drama">Drama</option>
                                <option value="Sci-Fi">Sci-Fi</option>
                                <option value="Thriller">Thriller</option>
                                <option value="Horror">Horror</option>
                                <option value="Romance">Romance</option>
                                <option value="Animation">Animation</option>
                                <option value="Documentary">Documentary</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                            <input
                                type="text"
                                value={filters.year}
                                onChange={(e) => handleFilterChange('year', e.target.value)}
                                placeholder="e.g. 2023"
                                className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
                            <select
                                value={filters.sort}
                                onChange={(e) => handleFilterChange('sort', e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="relevance">Relevance</option>
                                <option value="year">Year (newest first)</option>
                                <option value="rating">Rating (highest first)</option>
                            </select>
                        </div>
                    </div>
                )}
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                    {error}
                </div>
            )}

            {/* Results */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-6 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-800">
                        {query ? `Results for "${query}"` : 'Popular Movies & Shows'}
                    </h2>
                    <p className="text-gray-600 mt-1">
                        {sortedResults.length} {sortedResults.length === 1 ? 'result' : 'results'}
                    </p>
                </div>

                {isLoading ? (
                    <div className="p-6 text-center">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                        <p className="mt-2 text-gray-600">Searching...</p>
                    </div>
                ) : sortedResults.length > 0 ? (
                    <ul className="divide-y divide-gray-200">
                        {sortedResults.map((item, index) => (
                            <li key={index} className="p-6 hover:bg-gray-50 transition duration-150">
                                <div className="flex flex-col md:flex-row gap-4">
                                    <div className="h-36 w-24 bg-gray-200 flex items-center justify-center flex-shrink-0">
                                        <Film className="h-10 w-10 text-gray-400" />
                                    </div>
                                    <div className="flex-grow">
                                        <h3 className="font-medium text-lg text-gray-800">{item.title}</h3>
                                        <div className="flex items-center mt-1">
                                            <span className="text-sm text-gray-600 mr-3">{item.year}</span>
                                            <span className="text-sm bg-gray-200 px-2 py-1 rounded text-gray-700 mr-3">
                                                {item.media_type === 'movie' ? 'Movie' : 'TV Show'}
                                            </span>
                                            {item.rating && (
                                                <span className="flex items-center text-sm text-gray-700">
                                                    <Star className="h-4 w-4 text-yellow-500 mr-1" />
                                                    {item.rating}/10
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-gray-600 mt-2">{item.genres && item.genres.join(', ')}</p>
                                        <div className="flex mt-4 gap-2">
                                            <button className="bg-blue-600 text-white py-1 px-3 rounded text-sm hover:bg-blue-700">
                                                Details
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <div className="p-6 text-center text-gray-600">
                        {query ? 'No results found. Try a different search term.' : 'Search for movies and TV shows to see results.'}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MovieSearch;