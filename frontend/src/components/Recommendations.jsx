import React, { useState } from 'react';
import { getRecommendations } from '../services/Api';
import { ThumbsUp, Loader2 } from 'lucide-react';
import Markdown from 'react-markdown';

const Recommendations = () => {
    const [preferences, setPreferences] = useState('');
    const [recommendations, setRecommendations] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('custom');

    // options for the "Based on Mood" tab
    const moodOptions = [
        "Feel-good comedies for a rainy day",
        "Intense thrillers that will keep me on the edge of my seat",
        "Heartwarming family movies",
        "Mind-bending science fiction",
        "Inspiring true stories and biopics",
        "Dark and gritty crime dramas",
        "Emotional tearjerkers",
        "Action-packed adventures",
        "Thought-provoking psychological films",
        "Classic movies everyone should watch once"
    ];

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!preferences.trim()) return;

        setIsLoading(true);
        setRecommendations('');

        try {
            const response = await getRecommendations(preferences);
            setRecommendations(response.recommendations);
        } catch (error) {
            console.error('Error getting recommendations:', error);
            setRecommendations("Sorry, I encountered an error while getting recommendations. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleMoodSelect = (mood) => {
        setPreferences(mood);
        handleSubmit({ preventDefault: () => { } });
    };

    return (
        <div className="py-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Movie & TV Show Recommendations</h1>
                <p className="text-gray-600 mt-2">
                    Discover content tailored to your preferences
                </p>
            </header>

            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow mb-8">
                <div className="border-b border-gray-200">
                    <nav className="flex">
                        <button
                            onClick={() => setActiveTab('custom')}
                            className={`px-6 py-4 text-lg font-medium ${activeTab === 'custom'
                                ? 'border-b-2 border-blue-600 text-blue-600'
                                : 'text-gray-600 hover:text-gray-800'
                                }`}
                        >
                            Custom Preferences
                        </button>
                        <button
                            onClick={() => setActiveTab('mood')}
                            className={`px-6 py-4 text-lg font-medium ${activeTab === 'mood'
                                ? 'border-b-2 border-blue-600 text-blue-600'
                                : 'text-gray-600 hover:text-gray-800'
                                }`}
                        >
                            Based on Mood
                        </button>
                    </nav>
                </div>

                <div className="p-6">
                    {/* Custom Preferences Tab */}
                    {activeTab === 'custom' && (
                        <div>
                            <p className="mb-4 text-gray-700">
                                Describe what kind of movies or TV shows you're looking for, including genres, themes, or specific elements you enjoy.
                            </p>

                            <form onSubmit={handleSubmit}>
                                <div className="mb-4">
                                    <label htmlFor="preferences" className="block text-gray-700 font-medium mb-2">
                                        Your Preferences
                                    </label>
                                    <textarea
                                        id="preferences"
                                        value={preferences}
                                        onChange={(e) => setPreferences(e.target.value)}
                                        placeholder="e.g., I enjoy psychological thrillers with unexpected twists, similar to Fight Club or Shutter Island"
                                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px]"
                                        required
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={isLoading || !preferences.trim()}
                                    className="bg-blue-600 text-white py-2 px-6 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:bg-blue-400 disabled:cursor-not-allowed flex items-center"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="animate-spin h-5 w-5 mr-2" />
                                            Getting Recommendations...
                                        </>
                                    ) : (
                                        <>
                                            <ThumbsUp className="h-5 w-5 mr-2" />
                                            Get Recommendations
                                        </>
                                    )}
                                </button>
                            </form>
                        </div>
                    )}

                    {/* "Based on Mood" Tab */}
                    {activeTab === 'mood' && (
                        <div>
                            <p className="mb-4 text-gray-700">
                                Select a mood or vibe to get recommendations tailored to how you're feeling.
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                                {moodOptions.map((mood, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleMoodSelect(mood)}
                                        className="bg-gray-100 hover:bg-gray-200 p-4 rounded-lg text-left transition duration-200"
                                    >
                                        <p className="text-gray-800">{mood}</p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Recommendations Results */}
            {(recommendations || isLoading) && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                        <ThumbsUp className="h-5 w-5 mr-2 text-blue-600" />
                        Your Recommendations
                    </h2>

                    {isLoading ? (
                        <div className="flex justify-center items-center py-12">
                            <Loader2 className="animate-spin h-8 w-8 text-blue-600 mr-2" />
                            <span className="text-gray-600">Generating personalized recommendations...</span>
                        </div>
                    ) : (
                        <div className="prose max-w-none">
                            <Markdown>{recommendations}</Markdown>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Recommendations;