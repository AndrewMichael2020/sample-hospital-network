import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './NavHeader.css';

export const NavHeader: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/scenario-builder', label: 'Scenario Builder', key: 'builder' },
    { path: '/results', label: 'Results Dashboard', key: 'results' },
    { path: '/compare', label: 'Compare Scenarios', key: 'compare' },
  ];

  const isActive = (path: string) => {
    if (path === '/scenario-builder') {
      return location.pathname === '/scenario-builder' || location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <header className="nav-header">
      <div className="nav-container">
        <div className="nav-brand">
          <h1>Clinical Service Planning</h1>
          <span className="nav-subtitle">Healthcare Scenario Builder</span>
        </div>
        <nav className="nav-menu">
          {navItems.map((item) => (
            <Link
              key={item.key}
              to={item.path}
              className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
};