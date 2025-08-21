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

  const isNetworkError = (err: string | Error | ApiError): boolean => {
    const message = getErrorMessage(err).toLowerCase();
    return message.includes('network') || message.includes('fetch') || 
           message.includes('connection refused') || message.includes('failed to fetch');
  };

  const errorMessage = getErrorMessage(error);
  const isNetwork = isNetworkError(error);

  return (
    <div className={`error-state ${className}`}>
      <div className="error-icon">⚠️</div>
      <h3 className="error-title">{title}</h3>
      <p className="error-message">{errorMessage}</p>
      {isNetwork && (
        <div className="error-help">
          <p><strong>This appears to be a network connectivity issue.</strong></p>
          <p>Please ensure the backend API server is running on port 8080.</p>
          <details>
            <summary>How to start the API server</summary>
            <code>
              cd /path/to/project<br/>
              python3 mock_api.py
            </code>
          </details>
        </div>
      )}
      {showRetry && onRetry && (
        <button className="error-retry-btn" onClick={onRetry}>
          Try Again
        </button>
      )}
    </div>
  );
};