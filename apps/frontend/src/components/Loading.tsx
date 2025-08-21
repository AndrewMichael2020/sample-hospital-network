import React from 'react';
import './Loading.css';

interface LoadingProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

export const Loading: React.FC<LoadingProps> = ({ 
  message = 'Loading...', 
  size = 'medium',
  className = ''
}) => {
  return (
    <div className={`loading-container ${size} ${className}`}>
      <div className="loading-spinner" />
      <p className="loading-message">{message}</p>
    </div>
  );
};