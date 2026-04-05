import { apiRequest, transformMinioUrl } from '../client';
import { getServerHost, getApiBaseUrl } from '../../config/serverConfig';
import type { 
  MemberProfile, 
  CreateMemberDTO, 
  UpdateMemberDTO,
  DocumentRecord,
  ReviewTask,
  TrendSeries,
  VisionDashboard,
  GrowthDashboard,
  BloodDashboard,
  ExamRecord,
  RevisedItem
} from '../models';

export const memberService = {
  list: () => apiRequest<MemberProfile[]>('/members'),

  get: (id: string) => apiRequest<MemberProfile>(`/members/${id}`),

  create: (data: CreateMemberDTO) => 
    apiRequest<MemberProfile>('/members', { 
      method: 'POST', 
      body: JSON.stringify(data) 
    }),

  update: (id: string, data: UpdateMemberDTO) =>
    apiRequest<MemberProfile>(`/members/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiRequest<void>(`/members/${id}`, { method: 'DELETE' }),
};

export const documentService = {
  upload: async (file: { uri: string; type: string; name: string }, memberId: string) => {
    const formData = new FormData();
    formData.append('file', file as any);
    formData.append('member_id', memberId);

    const host = await getServerHost();
    const response = await fetch(
      `${getApiBaseUrl(host)}/api/v1/documents/upload`,
      {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }

    return response.json() as Promise<DocumentRecord & { file_url: string; desensitized_url: string }>;
  },

  get: (id: string) => apiRequest<DocumentRecord>(`/documents/${id}`),

  submitOcr: (id: string) => 
    apiRequest<{ document_id: string; status: string }>(`/documents/${id}/submit-ocr`, {
      method: 'POST',
    }),
};

export const reviewService = {
  list: (params?: { page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));
    const queryStr = query.toString();
    return apiRequest<ReviewTask[]>(`/review-tasks${queryStr ? `?${queryStr}` : ''}`);
  },

  get: (id: string) => apiRequest<ReviewTask>(`/review-tasks/${id}`),

  approve: (id: string, revisedItems: RevisedItem[]) =>
    apiRequest<{ status: string }>(`/review-tasks/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ revised_items: revisedItems }),
    }),

  reject: (id: string) =>
    apiRequest<{ status: string }>(`/review-tasks/${id}/reject`, {
      method: 'POST',
    }),

  saveDraft: (id: string, revisedItems: RevisedItem[]) =>
    apiRequest<{ status: string }>(`/review-tasks/${id}/save-draft`, {
      method: 'POST',
      body: JSON.stringify({ revised_items: revisedItems }),
    }),
};

export const trendService = {
  getTrends: (memberId: string, metric: string, range: string = '3m') =>
    apiRequest<TrendSeries>(`/members/${memberId}/trends?metric=${metric}&range=${range}`),

  getVisionDashboard: (memberId: string, range: string = '3m') =>
    apiRequest<VisionDashboard>(`/members/${memberId}/vision-dashboard?range=${range}`),

  getGrowthDashboard: (memberId: string, range: string = '3m') =>
    apiRequest<GrowthDashboard>(`/members/${memberId}/growth-dashboard?range=${range}`),

  getBloodDashboard: (memberId: string, range: string = '3m') =>
    apiRequest<BloodDashboard>(`/members/${memberId}/blood-dashboard?range=${range}`),
};

export const examService = {
  getRecord: (recordId: string) =>
    apiRequest<ExamRecord>(`/documents/records/${recordId}`),

  createManualExam: (memberId: string, data: {
    exam_date: string;
    institution_name?: string;
    observations: Array<{
      metric_code: string;
      value_numeric: number;
      unit: string;
      side?: string | null;
    }>;
  }) => apiRequest<ExamRecord>(`/records/members/${memberId}/manual-exams`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  deleteExamRecord: (recordId: string) =>
    apiRequest<void>(`/records/exam-records/${recordId}`, { method: 'DELETE' }),
};

export { transformMinioUrl };
