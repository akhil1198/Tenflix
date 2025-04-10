import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Film, Search, MessageSquare, ThumbsUp, BarChart2, Command } from 'lucide-react';

const Navbar = () => {
    const location = useLocation();

    return (
        <nav className="bg-gray-800 text-white p-4">
            <div className="container mx-auto flex justify-between items-center">
                <Link to="/" className="text-xl font-bold flex items-center">
                    <Command className="mr-2" /> Tenflix
                </Link>
                <div className="flex space-x-4">
                    <Link to="/search" className={`px-3 py-2 rounded hover:bg-gray-700 flex items-center ${location.pathname === '/search' ? 'bg-gray-700' : ''}`}>
                        <Search className="mr-1 h-4 w-4" /> Search
                    </Link>
                    <Link to="/chat" className={`px-3 py-2 rounded hover:bg-gray-700 flex items-center ${location.pathname === '/chat' ? 'bg-gray-700' : ''}`}>
                        <MessageSquare className="mr-1 h-4 w-4" /> Chat
                    </Link>
                    <Link to="/recommendations" className={`px-3 py-2 rounded hover:bg-gray-700 flex items-center ${location.pathname === '/recommendations' ? 'bg-gray-700' : ''}`}>
                        <ThumbsUp className="mr-1 h-4 w-4" /> Recommend
                    </Link>
                    <Link to="/compare" className={`px-3 py-2 rounded hover:bg-gray-700 flex items-center ${location.pathname === '/compare' ? 'bg-gray-700' : ''}`}>
                        <BarChart2 className="mr-1 h-4 w-4" /> Compare
                    </Link>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;