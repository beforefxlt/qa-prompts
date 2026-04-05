import { getServerHost, getApiBaseUrl, getMinioBaseUrl } from '../config/serverConfig';

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
  const host = await getServerHost();
  const url = `${getApiBaseUrl(host)}/api/v1${endpoint}`;
  
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

export function transformMinioUrl(minioUrl: string, host: string): string {
  if (!minioUrl) return '';
  if (minioUrl.startsWith('http')) return minioUrl;
  const key = minioUrl.replace('minio://', '');
  return `${getMinioBaseUrl(host)}${key}`;
}

export async function getDynamicMinioUrl(): Promise<string> {
  const host = await getServerHost();
  return getMinioBaseUrl(host);
}

export { apiRequest, ApiError };
