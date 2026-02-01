import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export const Header: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">W</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">Weave</h1>
            <span className="text-xs text-gray-500 ml-2">Worldview Explorer</span>
          </Link>

          <nav className="flex gap-1">
            <Link
              to="/"
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
            >
              Worldviews
            </Link>
            <Link
              to="/compare"
              className={`nav-link ${isActive('/compare') ? 'active' : ''}`}
            >
              Compare
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};
