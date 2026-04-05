// SSR (容器内): 使用 API_URL (Docker 内部网络 http://backend:8000)
// Client (浏览器): 使用 NEXT_PUBLIC_API_URL (外部可访问地址)
// 部署到服务器时，只需修改环境变量即可
const SSR_API_URL = process.env.API_URL;
const CLIENT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// 根据运行环境自动选择正确的 API 地址
const API_BASE_URL = (typeof window === 'undefined' && SSR_API_URL)
  ? SSR_API_URL + '/api/v1'
  : CLIENT_API_URL;

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
 * 包装 fetch 请求，捕获底层网络错误
 */
async function safeFetch(url: string, options?: RequestInit) {
  let finalUrl = url;
  const method = options?.method || 'GET';

  // [FORCE-PATH] 关键自愈逻辑：检测 8000 端口请求是否漏掉了 /api/v1 前缀
  if (finalUrl.includes(':8000') && !finalUrl.includes('/api/v1')) {
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
      throw new Error('网络连接失败，请确认后端 API 是否已运行');
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

  // Records & Manual Entry (CRUD)
  createManualExam: (memberId: string, data: any) =>
    safeFetch(`${API_BASE_URL}/records/members/${memberId}/manual-exams`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateObservation: (obsId: string, valueNumeric: number) =>
    safeFetch(`${API_BASE_URL}/records/observations/${obsId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value_numeric: valueNumeric }),
    }),

  deleteExamRecord: (recordId: string) =>
    safeFetch(`${API_BASE_URL}/records/exam-records/${recordId}`, {
      method: 'DELETE',
    }),

  // Trends
  getTrends: (memberId: string, metric: string) =>
    safeFetch(`${API_BASE_URL}/members/${memberId}/trends?metric=${metric}`),

  getVisionDashboard: (memberId: string) => safeFetch(`${API_BASE_URL}/members/${memberId}/vision-dashboard`),

  getGrowthDashboard: (memberId: string) => safeFetch(`${API_BASE_URL}/members/${memberId}/growth-dashboard`),

  getBloodDashboard: (memberId: string) => safeFetch(`${API_BASE_URL}/members/${memberId}/blood-dashboard`),

  getExamRecord: (recordId: string) => safeFetch(`${API_BASE_URL}/documents/records/${recordId}`),
};
