import { describe, it, expect } from 'vitest';
import { formatNumber, formatGap, formatFTE, validateOccupancyTarget, validateLOSDelta, validateALCTarget, validateGrowthRate } from '../lib/format';

describe('Format Utilities', () => {
  describe('formatNumber', () => {
    it('formats integers correctly', () => {
      expect(formatNumber(1234)).toBe('1,234');
      expect(formatNumber(0)).toBe('0');
      expect(formatNumber(5)).toBe('5');
    });

    it('formats decimals with options', () => {
      expect(formatNumber(1234.567, { maximumFractionDigits: 2 })).toBe('1,234.57');
      expect(formatNumber(1234.567, { maximumFractionDigits: 0 })).toBe('1,235');
    });
  });

  describe('formatGap', () => {
    it('formats positive numbers with + sign', () => {
      expect(formatGap(25)).toBe('+25');
      expect(formatGap(100)).toBe('+100');
    });

    it('formats negative numbers correctly', () => {
      expect(formatGap(-15)).toBe('-15');
      expect(formatGap(-200)).toBe('-200');
    });

    it('formats zero correctly', () => {
      expect(formatGap(0)).toBe('+0');
    });
  });

  describe('formatFTE', () => {
    it('formats FTE values with one decimal place', () => {
      expect(formatFTE(12.5)).toBe('12.5');
      expect(formatFTE(0.8)).toBe('0.8');
      expect(formatFTE(10)).toBe('10.0');
    });

    it('rounds to one decimal place', () => {
      expect(formatFTE(12.567)).toBe('12.6');
      expect(formatFTE(0.834)).toBe('0.8');
    });
  });
});

describe('Validation Utilities', () => {
  describe('validateOccupancyTarget', () => {
    it('returns null for valid values', () => {
      expect(validateOccupancyTarget(0.85)).toBeNull();
      expect(validateOccupancyTarget(0.5)).toBeNull();
      expect(validateOccupancyTarget(1.0)).toBeNull();
    });

    it('returns error for invalid values', () => {
      expect(validateOccupancyTarget(0.4)).toContain('between 50% and 100%');
      expect(validateOccupancyTarget(1.1)).toContain('between 50% and 100%');
    });
  });

  describe('validateLOSDelta', () => {
    it('returns null for valid values', () => {
      expect(validateLOSDelta(0.1)).toBeNull();
      expect(validateLOSDelta(-0.2)).toBeNull();
      expect(validateLOSDelta(0)).toBeNull();
    });

    it('returns error for invalid values', () => {
      expect(validateLOSDelta(0.6)).toContain('between -50% and +50%');
      expect(validateLOSDelta(-0.8)).toContain('between -50% and +50%');
    });
  });

  describe('validateALCTarget', () => {
    it('returns null for valid values', () => {
      expect(validateALCTarget(0.12)).toBeNull();
      expect(validateALCTarget(0)).toBeNull();
      expect(validateALCTarget(0.5)).toBeNull();
    });

    it('returns error for invalid values', () => {
      expect(validateALCTarget(-0.1)).toContain('between 0% and 50%');
      expect(validateALCTarget(0.6)).toContain('between 0% and 50%');
    });
  });

  describe('validateGrowthRate', () => {
    it('returns null for valid values', () => {
      expect(validateGrowthRate(0.05)).toBeNull();
      expect(validateGrowthRate(-0.1)).toBeNull();
      expect(validateGrowthRate(0)).toBeNull();
    });

    it('returns error for invalid values', () => {
      expect(validateGrowthRate(0.3)).toContain('between -20% and +20%');
      expect(validateGrowthRate(-0.25)).toContain('between -20% and +20%');
    });
  });
});