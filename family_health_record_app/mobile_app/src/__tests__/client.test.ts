import { transformMinioUrl } from '../api/client';
import { API_CONFIG } from '../constants/api';

describe('API Client - transformMinioUrl', () => {
  it('should return empty string for empty input', () => {
    expect(transformMinioUrl('')).toBe('');
    expect(transformMinioUrl(null as any)).toBe('');
    expect(transformMinioUrl(undefined as any)).toBe('');
  });

  it('should return original URL if already HTTP', () => {
    const httpUrl = 'http://localhost:9000/health-records/image.jpg';
    expect(transformMinioUrl(httpUrl)).toBe(httpUrl);
  });

  it('should return original URL if already HTTPS', () => {
    const httpsUrl = 'https://example.com/image.jpg';
    expect(transformMinioUrl(httpsUrl)).toBe(httpsUrl);
  });

  it('should transform minio URL to HTTP URL', () => {
    const minioUrl = 'minio://test.jpg';
    const expected = `${API_CONFIG.MINIO_BASE_URL}test.jpg`;
    expect(transformMinioUrl(minioUrl)).toBe(expected);
  });

  it('should handle minio URL with bucket prefix', () => {
    const minioUrl = 'minio://images/photo.jpg';
    const expected = `${API_CONFIG.MINIO_BASE_URL}images/photo.jpg`;
    expect(transformMinioUrl(minioUrl)).toBe(expected);
  });
});
