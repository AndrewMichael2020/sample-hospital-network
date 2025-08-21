import React from 'react';
import type { ApiError } from '../api/types';
import './ErrorState.css';

interface ErrorStateProps {
  error: string | Error | ApiError;
  title?: string;
  onRetry?: () => void;
  showRetry?: boolean;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  error,
  title = 'Something went wrong',
  onRetry,
  showRetry = true,
  className = ''
}) => {
  const getErrorMessage = (err: string | Error | ApiError): string => {
    if (typeof err === 'string') return err;
    if ('error' in err) return err.error; // ApiError
    return err.message; // Error
  };

  const errorMessage = getErrorMessage(error);

  return (
    <div className={`error-state ${className}`}>
      <div className="error-icon">⚠️</div>
      <h3 className="error-title">{title}</h3>
      <p className="error-message">{errorMessage}</p>
      {showRetry && onRetry && (
        <button className="error-retry-btn" onClick={onRetry}>
          Try Again
        </button>
      )}
    </div>
  );
};