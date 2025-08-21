import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { KpiCard } from '../components/KpiCard';

describe('KpiCard', () => {
  it('renders title and value correctly', () => {
    render(<KpiCard title="Total Beds" value={150} />);
    
    expect(screen.getByText('Total Beds')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('formats gap values with + sign', () => {
    render(<KpiCard title="Capacity Gap" value={25} format="gap" />);
    
    expect(screen.getByText('+25')).toBeInTheDocument();
  });

  it('formats negative gap values correctly', () => {
    render(<KpiCard title="Capacity Gap" value={-15} format="gap" />);
    
    expect(screen.getByText('-15')).toBeInTheDocument();
  });

  it('formats FTE values with decimal places', () => {
    render(<KpiCard title="Nursing FTE" value={12.5} format="fte" />);
    
    expect(screen.getByText('12.5')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(
      <KpiCard 
        title="Occupancy Rate" 
        value={85} 
        format="percent" 
        subtitle="Target: 90%"
      />
    );
    
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('Target: 90%')).toBeInTheDocument();
  });

  it('renders trend indicators', () => {
    render(
      <KpiCard 
        title="Census" 
        value={120} 
        trend="up"
      />
    );
    
    expect(screen.getByText('↑')).toBeInTheDocument();
  });

  it('handles null values gracefully', () => {
    render(<KpiCard title="Unknown Value" value={null} />);
    
    expect(screen.getByText('--')).toBeInTheDocument();
  });
});