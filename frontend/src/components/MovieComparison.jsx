import React, { useState } from 'react';
import { compareMovies } from '../services/Movies';
import { BarChart2, Film, X, Plus, Loader2 } from 'lucide-react';
import Markdown from 'react-markdown';

const MovieComparison = () => {
    const [titles, setTitles] = useState(['', '']);
    const [comparison, setComparison] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleAddTitle = () => {
        if (titles.length < 5) {
            setTitles([...titles, '']);
        }
    };

    const handleRemoveTitle = (index) => {
        if (titles.length > 2) {
            const newTitles = [...titles];
            newTitles.splice(index, 1);
            setTitles(newTitles);
        }
    };

    const handleTitleChange = (index, value) => {
        const newTitles = [...titles];
        newTitles[index] = value;
        setTitles(newTitles);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Validate titles
        const validTitles = titles.filter(title => title.trim());
        if (validTitles.length < 2) {
            setError('Please enter at least two movie or TV show titles to compare.');
            return;
        }

        setIsLoading(true);
        setError('');
        setComparison('');

        try {
            const response = await compareMovies(validTitles);
            setComparison(response.comparison);
        } catch (error) {
            console.error('Error comparing titles:', error);
            setError('An error occurred while comparing titles. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    // Presets for popular comparisons
    const popularComparisons = [
        ['The Godfather', 'Goodfellas', 'Scarface'],
        ['Lord of the Rings', 'Game of Thrones', 'The Witcher'],
        ['Breaking Bad', 'The Sopranos', 'The Wire'],
        ['Interstellar', 'Inception', 'The Matrix'],
        ['Star Wars', 'Star Trek']
    ];

    const handlePresetClick = (preset) => {
        setTitles(preset);
    };

    return (
        <div className="py-6">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Compare Movies & TV Shows</h1>
                <p className="text-gray-600 mt-2">
                    Analyze similarities and differences between your favorite titles
                </p>
            </header>

            {/* Comparison Form */}
            <div className="bg-white rounded-lg shadow p-6 mb-8">
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 font-medium mb-2">
                            Enter titles to compare:
                        </label>

                        {titles.map((title, index) => (
                            <div key={index} className="flex items-center mb-2">
                                <div className="mr-2 bg-blue-100 text-blue-800 w-6 h-6 rounded-full flex items-center justify-center">
                                    {index + 1}
                                </div>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => handleTitleChange(index, e.target.value)}
                                    placeholder={`Movie or TV show title ${index + 1}`}
                                    className="flex-grow px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    required={index < 2}
                                />
                                {titles.length > 2 && (
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveTitle(index)}
                                        className="ml-2 text-gray-500 hover:text-red-500"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                )}
                            </div>
                        ))}

                        {titles.length < 5 && (
                            <button
                                type="button"
                                onClick={handleAddTitle}
                                className="flex items-center text-blue-600 hover:text-blue-800 mt-2"
                            >
                                <Plus className="h-4 w-4 mr-1" />
                                Add another title
                            </button>
                        )}
                    </div>

                    {error && (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="bg-blue-600 text-white py-2 px-6 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:bg-blue-400 disabled:cursor-not-allowed flex items-center"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="animate-spin h-5 w-5 mr-2" />
                                Comparing...
                            </>
                        ) : (
                            <>
                                <BarChart2 className="h-5 w-5 mr-2" />
                                Compare
                            </>
                        )}
                    </button>
                </form>

                {/* Popular Comparisons */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                    <h3 className="font-medium text-gray-800 mb-2">Popular comparisons:</h3>
                    <div className="flex flex-wrap gap-2">
                        {popularComparisons.map((preset, index) => (
                            <button
                                key={index}
                                onClick={() => handlePresetClick(preset)}
                                className="bg-gray-100 hover:bg-gray-200 text-gray-800 py-1 px-3 rounded-full text-sm"
                            >
                                {preset.join(' vs ')}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Comparison Results */}
            {(comparison || isLoading) && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                        <BarChart2 className="h-5 w-5 mr-2 text-blue-600" />
                        Comparison Results
                    </h2>

                    {isLoading ? (
                        <div className="flex justify-center items-center py-12">
                            <Loader2 className="animate-spin h-8 w-8 text-blue-600 mr-2" />
                            <span className="text-gray-600">Analyzing and comparing titles...</span>
                        </div>
                    ) : (
                        <>
                            <div className="flex mb-6 overflow-x-auto">
                                {titles.filter(t => t.trim()).map((title, index) => (
                                    <div key={index} className="flex-shrink-0 flex flex-col items-center mr-4 p-4 bg-gray-50 rounded-lg min-w-[140px]">
                                        <div className="h-20 w-20 bg-gray-200 rounded-lg flex items-center justify-center mb-2">
                                            <Film className="h-10 w-10 text-gray-400" />
                                        </div>
                                        <span className="text-center font-medium text-gray-800">{title}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="prose max-w-none">
                                <Markdown>{comparison}</Markdown>
                            </div>
                        </>
                    )}
                </div>
            )}
        </div>
    );
};

export default MovieComparison;