const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

async function handleResponse(res: Response) {
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail || body.message || message;
    } catch { /* ignore */ }
    throw new Error(`API Error ${res.status}: ${message}`);
  }
  // 如果是 204 No Content，则不解析 JSON
  if (res.status === 204) {
    return null;
  }
  return res.json();
}

/**
 * 包装 fetch 请求，捕获底层网络错误（如后端未启动）
 * 注入 [AI-FLOW] 追踪逻辑以提升自动化测试的可观测性
 * 注入 [FORCE-PATH] 自愈逻辑以解决 Next.js 缓存顽疾导致的路径丢失
 */
async function safeFetch(url: string, options?: RequestInit) {
  let finalUrl = url;
  const method = options?.method || 'GET';

  // [FORCE-PATH] 关键自愈逻辑：检测 8000 端口请求是否漏掉了 /api/v1 前缀
  if (finalUrl.includes(':8000') && !finalUrl.includes('/api/v1')) {
     console.warn(`>> [AI-PATH-FIX] Detected potential missing prefix in ${finalUrl}. Attempting self-healing...`);
     finalUrl = finalUrl.replace(':8000', ':8000/api/v1');
  }

  console.log(`>> [AI-FLOW] Requesting: ${method} ${finalUrl}`);
  
  try {
    const res = await fetch(finalUrl, options);
    console.log(`<< [AI-FLOW] Response: ${res.status} for ${finalUrl}`);
    return await handleResponse(res);
  } catch (err: any) {
    console.error(`!! [AI-FLOW] Error for ${finalUrl}:`, err);
    if (err.message.includes('fetch') || err.message.includes('Failed to fetch')) {
      throw new Error('网络连接失败，请确认后端 API 是否在 8000 端口运行');
    }
    throw err;
  }
}

export const apiClient = {
  // Members
  getMembers: () => safeFetch(`${API_BASE_URL}/members`),

  getMember: (memberId: string) => safeFetch(`${API_BASE_URL}/members/${memberId}`),

  createMember: (data: { name: string; gender: string; date_of_birth: string; member_type: string }) => 
    safeFetch(`${API_BASE_URL}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateMember: (memberId: string, data: Partial<{ name: string; gender: string; date_of_birth: string; member_type: string }>) =>
    safeFetch(`${API_BASE_URL}/members/${memberId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteMember: (memberId: string) =>
    safeFetch(`${API_BASE_URL}/members/${memberId}`, {
      method: 'DELETE',
    }),

  // Documents
  uploadDocument: async (file: File, memberId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (memberId) {
      formData.append('member_id', memberId);
    }

    return safeFetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
  },

  getDocument: (documentId: string) => safeFetch(`${API_BASE_URL}/documents/${documentId}`),

  submitOcr: (documentId: string) =>
    safeFetch(`${API_BASE_URL}/documents/${documentId}/submit-ocr`, {
      method: 'POST',
    }),

  // Review Tasks
  getReviewTasks: () => safeFetch(`${API_BASE_URL}/review-tasks`),

  getReviewTask: (taskId: string) => safeFetch(`${API_BASE_URL}/review-tasks/${taskId}`),

  approveReviewTask: (taskId: string, revisedItems?: any[]) =>
    safeFetch(`${API_BASE_URL}/review-tasks/${taskId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revised_items: revisedItems || [] }),
    }),

  rejectReviewTask: (taskId: string) =>
    safeFetch(`${API_BASE_URL}/review-tasks/${taskId}/reject`, {
      method: 'POST',
    }),

  saveDraftReviewTask: (taskId: string, revisedItems?: any[]) =>
    safeFetch(`${API_BASE_URL}/review-tasks/${taskId}/save-draft`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revised_items: revisedItems || [] }),
    }),

  // Trends
  getTrends: (memberId: string, metric: string) =>
    safeFetch(`${API_BASE_URL}/members/${memberId}/trends?metric=${metric}`),

  getVisionDashboard: (memberId: string) => safeFetch(`${API_BASE_URL}/members/${memberId}/vision-dashboard`),

  getGrowthDashboard: (memberId: string) => safeFetch(`${API_BASE_URL}/members/${memberId}/growth-dashboard`),

  getExamRecord: (recordId: string) => safeFetch(`${API_BASE_URL}/documents/records/${recordId}`),
};
