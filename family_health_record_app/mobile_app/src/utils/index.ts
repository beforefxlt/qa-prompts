import { METRIC_RANGES } from '../constants/api';

export function calculateAge(dateOfBirth: string | Date): number {
  const birth = typeof dateOfBirth === 'string' ? new Date(dateOfBirth) : dateOfBirth;
  const today = new Date();
  
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  return age;
}

export function inferMemberType(dateOfBirth: string | Date): 'child' | 'adult' | 'senior' {
  const age = calculateAge(dateOfBirth);
  
  if (age < 18) return 'child';
  if (age < 60) return 'adult';
  return 'senior';
}

export function getConfidenceStyle(score: number): {
  bg: string;
  text: string;
  label: string;
} {
  if (score >= 0.8) {
    return { bg: '#E8F5E9', text: '#2E7D32', label: '识别可信' };
  }
  if (score >= 0.6) {
    return { bg: '#FFF3CD', text: '#856404', label: '请核对关键字段' };
  }
  return { bg: '#FFEBEE', text: '#C62828', label: '识别置信度低，请仔细核对' };
}

export interface TrendPoint {
  date: string;
  value: number;
  side?: 'left' | 'right' | null;
}

export interface ComparisonResult {
  current: number;
  previous: number;
  delta: number;
}

export interface DualComparisonResult {
  left: ComparisonResult;
  right: ComparisonResult;
}

export function calculateGrowthRate(series: TrendPoint[]): number | null {
  if (series.length < 2) return null;
  
  const sorted = [...series].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  
  if (first.date === last.date) return null;
  
  const firstDate = new Date(first.date);
  const lastDate = new Date(last.date);
  const yearsDiff = (lastDate.getTime() - firstDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
  
  if (yearsDiff === 0) return null;
  
  return (last.value - first.value) / yearsDiff;
}

export function calculateComparison(series: TrendPoint[]): ComparisonResult | DualComparisonResult | null {
  if (series.length < 2) return null;
  
  const sorted = [...series].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  const latest = sorted[sorted.length - 1];
  const previous = sorted[sorted.length - 2];
  
  if (latest.date === previous.date) return null;
  
  if (latest.side && previous.side) {
    if (latest.side === 'left' && previous.side === 'left') {
      return {
        current: latest.value,
        previous: previous.value,
        delta: latest.value - previous.value,
      };
    }
    if (latest.side === 'right' && previous.side === 'right') {
      return {
        current: latest.value,
        previous: previous.value,
        delta: latest.value - previous.value,
      };
    }
  }
  
  if (!latest.side && !previous.side) {
    return {
      current: latest.value,
      previous: previous.value,
      delta: latest.value - previous.value,
    };
  }
  
  const leftSeries = sorted.filter(s => s.side === 'left');
  const rightSeries = sorted.filter(s => s.side === 'right');
  
  if (leftSeries.length >= 2 && rightSeries.length >= 2) {
    const leftLatest = leftSeries[leftSeries.length - 1];
    const leftPrev = leftSeries[leftSeries.length - 2];
    const rightLatest = rightSeries[rightSeries.length - 1];
    const rightPrev = rightSeries[rightSeries.length - 2];
    
    return {
      left: {
        current: leftLatest.value,
        previous: leftPrev.value,
        delta: leftLatest.value - leftPrev.value,
      },
      right: {
        current: rightLatest.value,
        previous: rightPrev.value,
        delta: rightLatest.value - rightPrev.value,
      },
    };
  }
  
  return {
    current: latest.value,
    previous: previous.value,
    delta: latest.value - previous.value,
  };
}

export function validateMetricValue(metricCode: string, value: number): boolean {
  const range = METRIC_RANGES[metricCode as keyof typeof METRIC_RANGES];
  if (!range) return true;
  return value >= range.min && value <= range.max;
}

export function validateRequired(value: string | null | undefined): boolean {
  if (value === null || value === undefined) return false;
  return value.trim().length > 0;
}

export function validateDateFormat(dateStr: string): boolean {
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateStr)) return false;
  
  const date = new Date(dateStr);
  return !isNaN(date.getTime());
}

export function validateFutureDate(dateStr: string): boolean {
  const date = new Date(dateStr);
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  return date > today;
}

export function validatePastDate(dateStr: string, minYear: number = 1900): boolean {
  const date = new Date(dateStr);
  return date.getFullYear() >= minYear && date < new Date();
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toISOString().split('T')[0];
}

export function formatChineseDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}年${month}月${day}日`;
}

export function resolveImageUrl(
  fileUrl: string | undefined,
  documentId: string | undefined,
  minioBaseUrl: string
): string {
  if (fileUrl && fileUrl.startsWith('http')) return fileUrl;
  if (fileUrl && fileUrl.startsWith('minio://')) {
    return `${minioBaseUrl}${fileUrl.replace('minio://', '')}`;
  }
  if (documentId) return `${minioBaseUrl}${documentId}`;
  return '';
}

export function getLatestValue(series: TrendPoint[]): TrendPoint | null {
  if (!series?.length) return null;
  const sorted = [...series].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  return sorted[sorted.length - 1];
}

export function shouldShowEmptyState(
  isChild: boolean,
  hasVisionData: boolean,
  hasGrowthData: boolean,
  pendingReviewCount: number
): boolean {
  const hasAnyData = (isChild && (hasVisionData || hasGrowthData)) || (!isChild && hasVisionData);
  return !hasAnyData && pendingReviewCount === 0;
}

export function splitSeriesBySide(series: TrendPoint[]): {
  leftData: TrendPoint[];
  rightData: TrendPoint[];
  labels: string[];
} {
  const leftData = series.filter(s => s.side === 'left' || !s.side);
  const rightData = series.filter(s => s.side === 'right');
  const allDates = [...new Set(series.map(s => s.date))].sort();
  return { leftData, rightData, labels: allDates };
}
