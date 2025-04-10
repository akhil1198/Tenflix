import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, Info, ThumbsUp, Loader2 } from 'lucide-react';

import Markdown from 'react-markdown';
import { queryInformation } from '../services/Movies';

const MovieChat = () => {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hi there! I'm your movie and TV show assistant. Ask me anything about movies, shows, actors, directors, or get recommendations based on your preferences."
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const suggestions = [
        "What are some good sci-fi movies from the 90s?",
        "Compare The Godfather and Goodfellas",
        "Tell me about shows similar to Breaking Bad",
        "Who directed Inception and what other films did they make?",
        "What are the best comedy movies of 2023?",
    ];

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!input.trim()) return;

        const userMessage = {
            role: 'user',
            content: input
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await queryInformation(input)

            setTimeout(() => {
                setMessages(prev => [
                    ...prev,
                    {
                        role: 'assistant',
                        content: response.answer
                    }
                ]);
                setIsLoading(false);
            }, 500); // Small delay to make the interaction feel more natural

        } catch (error) {
            console.error('Error querying information:', error);

            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: "I'm sorry, I encountered an error while processing your request. Please try again."
                }
            ]);
            setIsLoading(false);
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setInput(suggestion);
    };

    return (
        <div className="py-6 flex flex-col h-[calc(100vh-120px)]">
            <header className="mb-4">
                <h1 className="text-3xl font-bold text-gray-800">Ask AI for Movie & TV Shows</h1>
                <p className="text-gray-600 mt-2">
                    Ask questions and get AI-powered answers about movies and shows
                </p>
            </header>

            {/* Chat Interface */}
            <div className="bg-white rounded-lg shadow flex flex-col flex-grow overflow-hidden">
                {/* Messages */}
                <div className="flex-grow overflow-y-auto p-6">
                    <div className="space-y-4">
                        {messages.map((message, index) => (
                            <div
                                key={index}
                                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-3/4 rounded-lg p-4 ${message.role === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-800'
                                        }`}
                                >
                                    <div className="flex items-center mb-2">
                                        {message.role === 'user' ? (
                                            <>
                                                <span className="font-medium">You</span>
                                            </>
                                        ) : (
                                            <>
                                                <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
                                                <span className="font-medium">Movie Assistant</span>
                                            </>
                                        )}
                                    </div>

                                    <div className={` ${message.role === 'user' ? 'text-white' : 'text-gray-800'}`}>
                                        <Markdown>{message.content}</Markdown>
                                    </div>
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-gray-100 rounded-lg p-4 text-gray-800 flex items-center">
                                    <Loader2 className="h-5 w-5 mr-2 animate-spin text-blue-600" />
                                    <span>Thinking...</span>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Suggestions */}
                {messages.length < 3 && (
                    <div className="px-6 py-3 border-t border-gray-200">
                        <div className="text-sm text-gray-600 mb-2 flex items-center">
                            <Info className="h-4 w-4 mr-1" />
                            Try asking:
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {suggestions.map((suggestion, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSuggestionClick(suggestion)}
                                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 text-sm py-1 px-3 rounded-full"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Input Form */}
                <div className="p-4 border-t border-gray-200">
                    <form onSubmit={handleSubmit} className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about movies or TV shows..."
                            className="flex-grow p-2 border border-gray-300 rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="bg-blue-600 text-white py-2 px-4 rounded-r hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed flex items-center"
                        >
                            <Send className="h-5 w-5" />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default MovieChat;