const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = {
  getMembers: async () => {
    const res = await fetch(`${API_BASE_URL}/members`);
    if (!res.ok) throw new Error('Failed to fetch members');
    return res.json();
  },
  
  getTrends: async (memberId: string, metric: string) => {
    const res = await fetch(`${API_BASE_URL}/members/${memberId}/trends?metric=${metric}`);
    if (!res.ok) throw new Error('Failed to fetch trends');
    return res.json();
  },
  
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
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  }
};
