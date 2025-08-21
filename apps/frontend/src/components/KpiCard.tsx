import React from 'react';
import { formatNumber, formatGap, formatFTE } from '../lib/format';
import './KpiCard.css';

interface KpiCardProps {
  title: string;
  value: number | string | null | undefined;
  format?: 'number' | 'gap' | 'fte' | 'percent' | 'custom';
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  format = 'number',
  subtitle,
  trend,
  className = ''
}) => {
  const formatValue = (val: number | string | null | undefined): string => {
    if (val == null) return '--';
    if (typeof val === 'string') return val;
    
    switch (format) {
      case 'gap':
        return formatGap(val);
      case 'fte':
        return formatFTE(val);
      case 'percent':
        return `${formatNumber(val, { maximumFractionDigits: 1 })}%`;
      case 'number':
      default:
        return formatNumber(val, { maximumFractionDigits: 0 });
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return '↑';
      case 'down':
        return '↓';
      default:
        return '';
    }
  };

  const getTrendClass = () => {
    switch (trend) {
      case 'up':
        return 'trend-up';
      case 'down':
        return 'trend-down';
      default:
        return '';
    }
  };

  return (
    <div className={`kpi-card ${className}`}>
      <div className="kpi-header">
        <h3 className="kpi-title">{title}</h3>
        {trend && (
          <span className={`kpi-trend ${getTrendClass()}`}>
            {getTrendIcon()}
          </span>
        )}
      </div>
      <div className="kpi-value">{formatValue(value)}</div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
    </div>
  );
};