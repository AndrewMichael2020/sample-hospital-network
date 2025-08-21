import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Loading } from '../components/Loading';

describe('Loading', () => {
  it('renders with default message', () => {
    render(<Loading />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<Loading message="Fetching data..." />);
    
    expect(screen.getByText('Fetching data...')).toBeInTheDocument();
  });

  it('applies correct size class', () => {
    const { container } = render(<Loading size="large" />);
    const loadingContainer = container.querySelector('.loading-container');
    
    expect(loadingContainer).toHaveClass('large');
  });

  it('applies custom className', () => {
    const { container } = render(<Loading className="custom-loading" />);
    const loadingContainer = container.querySelector('.loading-container');
    
    expect(loadingContainer).toHaveClass('custom-loading');
  });

  it('renders spinner element', () => {
    const { container } = render(<Loading />);
    const spinner = container.querySelector('.loading-spinner');
    
    expect(spinner).toBeInTheDocument();
  });
});