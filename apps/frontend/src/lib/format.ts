/**
 * Formatting utilities for the frontend
 */

export const formatNumber = (
  value: number,
  options?: Intl.NumberFormatOptions
): string => {
  return new Intl.NumberFormat('en-CA', options).format(value);
};

export const formatGap = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${formatNumber(value)}`;
};

export const formatFTE = (value: number): string => {
  return formatNumber(value, { 
    minimumFractionDigits: 1, 
    maximumFractionDigits: 1 
  });
};

/**
 * Validation utilities for form inputs
 */

export const validateOccupancyTarget = (value: number): string | null => {
  if (value < 0.5 || value > 1.0) {
    return 'Occupancy target must be between 50% and 100%';
  }
  return null;
};

export const validateLOSDelta = (value: number): string | null => {
  if (value < -0.5 || value > 0.5) {
    return 'LOS delta must be between -50% and +50%';
  }
  return null;
};

export const validateALCTarget = (value: number): string | null => {
  if (value < 0 || value > 0.5) {
    return 'ALC target must be between 0% and 50%';
  }
  return null;
};

export const validateGrowthRate = (value: number): string | null => {
  if (value < -0.2 || value > 0.2) {
    return 'Growth rate must be between -20% and +20%';
  }
  return null;
};