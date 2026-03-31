const API_BASE_URL = 'http://localhost:8000/api/v1';

async function handleResponse(res: Response) {
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail || body.message || message;
    } catch { /* ignore */ }
    throw new Error(`API Error ${res.status}: ${message}`);
  }
  return res.json();
}

export const apiClient = {
  // Members
  getMembers: async () => {
    const res = await fetch(`${API_BASE_URL}/members`);
    return handleResponse(res);
  },

  getMember: async (memberId: string) => {
    const res = await fetch(`${API_BASE_URL}/members/${memberId}`);
    return handleResponse(res);
  },

  createMember: async (data: { name: string; gender: string; date_of_birth: string; member_type: string }) => {
    const res = await fetch(`${API_BASE_URL}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  updateMember: async (memberId: string, data: Partial<{ name: string; gender: string; date_of_birth: string; member_type: string }>) => {
    const res = await fetch(`${API_BASE_URL}/members/${memberId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  deleteMember: async (memberId: string) => {
    const res = await fetch(`${API_BASE_URL}/members/${memberId}`, {
      method: 'DELETE',
    });
    return handleResponse(res);
  },

  // Documents
  uploadDocument: async (file: File, memberId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (memberId) {
      formData.append('member_id', memberId);
    }

    const res = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  getDocument: async (documentId: string) => {
    const res = await fetch(`${API_BASE_URL}/documents/${documentId}`);
    return handleResponse(res);
  },

  submitOcr: async (documentId: string) => {
    const res = await fetch(`${API_BASE_URL}/documents/${documentId}/submit-ocr`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  // Review Tasks
  getReviewTasks: async () => {
    const res = await fetch(`${API_BASE_URL}/review-tasks`);
    return handleResponse(res);
  },

  getReviewTask: async (taskId: string) => {
    const res = await fetch(`${API_BASE_URL}/review-tasks/${taskId}`);
    return handleResponse(res);
  },

  approveReviewTask: async (taskId: string, revisedItems?: any[]) => {
    const res = await fetch(`${API_BASE_URL}/review-tasks/${taskId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revised_items: revisedItems || [] }),
    });
    return handleResponse(res);
  },

  rejectReviewTask: async (taskId: string) => {
    const res = await fetch(`${API_BASE_URL}/review-tasks/${taskId}/reject`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  saveDraftReviewTask: async (taskId: string, revisedItems?: any[]) => {
    const res = await fetch(`${API_BASE_URL}/review-tasks/${taskId}/save-draft`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revised_items: revisedItems || [] }),
    });
    return handleResponse(res);
  },

  // Trends
  getTrends: async (memberId: string, metric: string) => {
    const res = await fetch(`${API_BASE_URL}/members/${memberId}/trends?metric=${metric}`);
    return handleResponse(res);
  },

  getVisionDashboard: async (memberId: string) => {
    const res = await fetch(`${API_BASE_URL}/members/${memberId}/vision-dashboard`);
    return handleResponse(res);
  },

  getGrowthDashboard: async (memberId: string) => {
    const res = await fetch(`${API_BASE_URL}/members/${memberId}/growth-dashboard`);
    return handleResponse(res);
  },
};
