import { API_CONFIG } from '../constants/api';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_CONFIG.BASE_URL}${API_CONFIG.API_PREFIX}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    try {
      const error = await response.json();
      errorMessage = error.detail || errorMessage;
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(response.status, errorMessage);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

export function transformMinioUrl(minioUrl: string): string {
  if (!minioUrl) return '';
  if (minioUrl.startsWith('http')) return minioUrl;
  const key = minioUrl.replace('minio://', '');
  return `${API_CONFIG.MINIO_BASE_URL}${key}`;
}

export { apiRequest, ApiError };
