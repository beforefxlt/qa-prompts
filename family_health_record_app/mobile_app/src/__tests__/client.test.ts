import { transformMinioUrl } from '../api/client';

const testHost = '10.0.2.2';

describe('API Client - transformMinioUrl', () => {
  it('should return empty string for empty input', () => {
    expect(transformMinioUrl('', testHost)).toBe('');
    expect(transformMinioUrl(null as any, testHost)).toBe('');
    expect(transformMinioUrl(undefined as any, testHost)).toBe('');
  });

  it('should return original URL if already HTTP', () => {
    const httpUrl = 'http://localhost:9000/health-records/image.jpg';
    expect(transformMinioUrl(httpUrl, testHost)).toBe(httpUrl);
  });

  it('should return original URL if already HTTPS', () => {
    const httpsUrl = 'https://example.com/image.jpg';
    expect(transformMinioUrl(httpsUrl, testHost)).toBe(httpsUrl);
  });

  it('should transform minio URL to HTTP URL', () => {
    const minioUrl = 'minio://test.jpg';
    const expected = `http://${testHost}:9000/health-records/test.jpg`;
    expect(transformMinioUrl(minioUrl, testHost)).toBe(expected);
  });

  it('should handle minio URL with bucket prefix', () => {
    const minioUrl = 'minio://images/photo.jpg';
    const expected = `http://${testHost}:9000/health-records/images/photo.jpg`;
    expect(transformMinioUrl(minioUrl, testHost)).toBe(expected);
  });
});
