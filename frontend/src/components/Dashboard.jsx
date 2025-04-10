import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { searchMovies } from '../services/Api';
import {
    Search, MessageSquare, ThumbsUp, BarChart2, Film, Star
} from 'lucide-react';

const Dashboard = () => {
    const [trendingMovies, setTrendingMovies] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchTrending = async () => {
            try {
                const trendingData = await searchMovies('popular trending movies');
                setTrendingMovies(trendingData.results.slice(0, 5));
            } catch (error) {
                console.error('Error fetching trending movies:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchTrending();
    }, []);

    return (
        <div className="py-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Welcome to Tenflix</h1>
                <p className="text-gray-600 mt-2">
                    Your AI-powered movie and TV show recommendation system
                </p>
            </header>

            <section className="mb-10">
                <h2 className="text-xl font-semibold mb-4 text-gray-700">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Link
                        to="/search"
                        className="bg-white rounded-lg shadow p-6 flex items-center hover:bg-gray-50 transition duration-200"
                    >
                        <Search className="h-8 w-8 text-blue-500 mr-4" />
                        <div>
                            <h3 className="font-medium text-lg">Search</h3>
                            <p className="text-gray-600">Find movies and shows</p>
                        </div>
                    </Link>

                    <Link
                        to="/chat"
                        className="bg-white rounded-lg shadow p-6 flex items-center hover:bg-gray-50 transition duration-200"
                    >
                        <MessageSquare className="h-8 w-8 text-green-500 mr-4" />
                        <div>
                            <h3 className="font-medium text-lg">Chat</h3>
                            <p className="text-gray-600">Ask about movies</p>
                        </div>
                    </Link>

                    <Link
                        to="/recommendations"
                        className="bg-white rounded-lg shadow p-6 flex items-center hover:bg-gray-50 transition duration-200"
                    >
                        <ThumbsUp className="h-8 w-8 text-purple-500 mr-4" />
                        <div>
                            <h3 className="font-medium text-lg">Recommendations</h3>
                            <p className="text-gray-600">Get personalized picks</p>
                        </div>
                    </Link>

                    <Link
                        to="/compare"
                        className="bg-white rounded-lg shadow p-6 flex items-center hover:bg-gray-50 transition duration-200"
                    >
                        <BarChart2 className="h-8 w-8 text-orange-500 mr-4" />
                        <div>
                            <h3 className="font-medium text-lg">Compare</h3>
                            <p className="text-gray-600">Compare titles</p>
                        </div>
                    </Link>
                </div>
            </section>

            {/* Trending Movies */}
            <section className="mb-10">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold text-gray-700">Trending Movies</h2>
                    <Link to="/search?query=trending" className="text-blue-600 hover:underline">See all</Link>
                </div>

                {isLoading ? (
                    <div className="text-center py-8">Loading trending movies...</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                        {trendingMovies.length > 0 ? (
                            trendingMovies.map((movie, index) => (
                                <div key={index} className="bg-white rounded-lg shadow overflow-hidden">
                                    <div className="h-40 bg-gray-200 flex items-center justify-center">
                                        <Film className="h-16 w-16 text-gray-400" />
                                    </div>
                                    <div className="p-4">
                                        <h3 className="font-medium text-gray-800 truncate">{movie.title}</h3>
                                        <p className="text-gray-600 text-sm">{movie.year} • {movie.media_type}</p>
                                        <div className="flex items-center mt-2">
                                            <Star className="h-4 w-4 text-yellow-500 mr-1" />
                                            <span className="text-sm text-gray-700">8.5/10</span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="col-span-5 text-center py-8 text-gray-600">
                                No trending movies available right now
                            </div>
                        )}
                    </div>
                )}
            </section>

            {/* About RAG */}
            <section className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">About This Project</h2>
                <p className="text-gray-700 mb-3">
                    Tenflix is a Movie Recommendation System that showcases Retrieval-Augmented Generation (RAG) technology, combining:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700 space-y-1">
                    <li>Vector search for finding semantically similar content</li>
                    <li>Large Language Model integration for natural conversations</li>
                    <li>Content-based recommendations powered by AI</li>
                    <li>Data from multiple movie databases (IMDb, TMDB, MovieLens)</li>
                </ul>
                <p className="text-gray-700">
                    Try asking specific questions, to get personalized recommendations, or comparing movies to see RAG in action! This is still a work in progress!
                </p>
            </section>
        </div>
    );
};

export default Dashboard;