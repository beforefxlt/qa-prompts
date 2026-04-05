import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = '@server_host';
const DEFAULT_HOST = '10.0.2.2';

let cachedHost: string | null = null;

export async function getServerHost(): Promise<string> {
  if (cachedHost) return cachedHost;
  try {
    const host = await AsyncStorage.getItem(STORAGE_KEY);
    cachedHost = host || DEFAULT_HOST;
  } catch {
    cachedHost = DEFAULT_HOST;
  }
  return cachedHost;
}

export async function setServerHost(host: string): Promise<void> {
  const normalized = host.replace(/^https?:\/\//, '').replace(/\/+$/, '');
  cachedHost = normalized;
  await AsyncStorage.setItem(STORAGE_KEY, normalized);
}

export function getApiBaseUrl(host: string): string {
  return `http://${host}:8000`;
}

export function getMinioBaseUrl(host: string): string {
  return `http://${host}:9000/health-records/`;
}

export async function getApiUrl(): Promise<string> {
  const host = await getServerHost();
  return `${getApiBaseUrl(host)}/api/v1`;
}

export async function getMinioUrl(): Promise<string> {
  const host = await getServerHost();
  return getMinioBaseUrl(host);
}

export async function testConnection(host?: string): Promise<{ ok: boolean; message: string }> {
  const rawHost = host || (await getServerHost());
  const targetHost = rawHost.replace(/^https?:\/\//, '').replace(/\/+$/, '');
  const url = `${getApiBaseUrl(targetHost)}/api/v1/health`;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (response.ok) {
      const data = await response.json();
      return { ok: true, message: `已连接 (v${data.version || 'unknown'})` };
    }
    return { ok: false, message: `响应异常: HTTP ${response.status}` };
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      return { ok: false, message: '连接超时' };
    }
    return { ok: false, message: `无法连接 (${targetHost}:8000)` };
  }
}
