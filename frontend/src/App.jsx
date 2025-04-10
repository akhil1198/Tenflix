import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import MovieSearch from './components/MovieSearch';
import MovieChat from './components/MovieChat';
import Recommendations from './components/Recommendations';
import MovieComparison from './components/MovieComparison';

import './index.css';

const App = () => {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="container mx-auto mt-4 px-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<MovieSearch />} />
            <Route path="/chat" element={<MovieChat />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/compare" element={<MovieComparison />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;