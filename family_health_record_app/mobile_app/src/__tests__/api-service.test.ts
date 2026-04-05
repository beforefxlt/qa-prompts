global.fetch = jest.fn();

const mockFetch = global.fetch as jest.Mock;

beforeEach(() => {
  mockFetch.mockClear();
});

describe('API 服务层 - MemberService', () => {
  const BASE_URL = 'http://10.0.2.2:8000';

  describe('memberService.list', () => {
    it('成功返回成员列表', async () => {
      const mockMembers = [
        {
          id: '1',
          name: '张三',
          gender: 'male',
          date_of_birth: '2018-06-15',
          member_type: 'child',
          last_check_date: '2026-03-29',
          pending_review_count: 2,
        },
        {
          id: '2',
          name: '李四',
          gender: 'female',
          date_of_birth: '1990-01-01',
          member_type: 'adult',
          last_check_date: null,
          pending_review_count: 0,
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMembers),
      });

      const { memberService } = await import('../api/services');
      const result = await memberService.list();

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/members`,
        expect.any(Object)
      );
      expect(result).toEqual(mockMembers);
      expect(result).toHaveLength(2);
    });

    it('返回空数组', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const { memberService } = await import('../api/services');
      const result = await memberService.list();

      expect(result).toEqual([]);
    });

    it('网络错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network request failed'));

      const { memberService } = await import('../api/services');
      
      await expect(memberService.list()).rejects.toThrow('Network request failed');
    });
  });

  describe('memberService.get', () => {
    it('成功获取单个成员', async () => {
      const mockMember = {
        id: '1',
        name: '张三',
        gender: 'male',
        date_of_birth: '2018-06-15',
        member_type: 'child',
        last_check_date: '2026-03-29',
        pending_review_count: 2,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMember),
      });

      const { memberService } = await import('../api/services');
      const result = await memberService.get('1');

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/members/1`,
        expect.any(Object)
      );
      expect(result.name).toBe('张三');
    });

    it('404 成员不存在', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Member not found' }),
      });

      const { memberService } = await import('../api/services');
      
      await expect(memberService.get('999')).rejects.toThrow('Member not found');
    });
  });

  describe('memberService.create', () => {
    it('成功创建成员', async () => {
      const newMember = {
        name: '王五',
        gender: 'male' as const,
        date_of_birth: '2020-01-01',
        member_type: 'child' as const,
      };

      const createdMember = { id: '3', ...newMember };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(createdMember),
      });

      const { memberService } = await import('../api/services');
      const result = await memberService.create(newMember);

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/members`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newMember),
        })
      );
      expect(result.id).toBe('3');
    });

    it('400 错误 - 必填字段缺失', async () => {
      const invalidMember = {
        name: '',
        gender: 'male',
        date_of_birth: '2020-01-01',
        member_type: 'child',
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'name is required' }),
      });

      const { memberService } = await import('../api/services');
      
      await expect(memberService.create(invalidMember as any)).rejects.toThrow('name is required');
    });
  });

  describe('memberService.update', () => {
    it('成功更新成员', async () => {
      const updateData = { name: '张三（更新）' };
      const updatedMember = {
        id: '1',
        name: '张三（更新）',
        gender: 'male',
        date_of_birth: '2018-06-15',
        member_type: 'child',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedMember),
      });

      const { memberService } = await import('../api/services');
      const result = await memberService.update('1', updateData);

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/members/1`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      );
      expect(result.name).toBe('张三（更新）');
    });
  });

  describe('memberService.delete', () => {
    it('成功删除成员 (软删除)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      });

      const { memberService } = await import('../api/services');
      const result = await memberService.delete('1');

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/members/1`,
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });
});

describe('API 服务层 - ReviewService', () => {
  const BASE_URL = 'http://10.0.2.2:8000';

  describe('reviewService.list', () => {
    it('成功获取审核列表', async () => {
      const mockTasks = [
        {
          id: 'task-1',
          document_id: 'doc-1',
          member_id: 'mem-1',
          status: 'pending',
          ocr_result: {
            exam_date: '2026-03-29',
            observations: [],
            confidence_score: 0.85,
          },
          revised_items: [],
          created_at: '2026-03-29T10:00:00Z',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTasks),
      });

      const { reviewService } = await import('../api/services');
      const result = await reviewService.list();

      expect(result).toHaveLength(1);
      expect(result[0].status).toBe('pending');
    });

    it('分页参数', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const { reviewService } = await import('../api/services');
      await reviewService.list({ page: 2, page_size: 10 });

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/review-tasks?page=2&page_size=10`,
        expect.any(Object)
      );
    });

    it('返回空数组', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const { reviewService } = await import('../api/services');
      const result = await reviewService.list();

      expect(result).toEqual([]);
    });
  });

  describe('reviewService.get', () => {
    it('成功获取审核详情', async () => {
      const mockTask = {
        id: 'task-1',
        document_id: 'doc-1',
        member_id: 'mem-1',
        status: 'pending',
        ocr_result: {
          exam_date: '2026-03-29',
          observations: [
            { metric_code: 'height', value_numeric: 120, unit: 'cm' },
          ],
          confidence_score: 0.85,
        },
        revised_items: [],
        created_at: '2026-03-29T10:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTask),
      });

      const { reviewService } = await import('../api/services');
      const result = await reviewService.get('task-1');

      expect(result.id).toBe('task-1');
      expect(result.ocr_result.observations).toHaveLength(1);
    });

    it('404 任务不存在', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Task not found' }),
      });

      const { reviewService } = await import('../api/services');
      
      await expect(reviewService.get('999')).rejects.toThrow('Task not found');
    });
  });

  describe('reviewService.approve', () => {
    it('成功审核通过', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'approved' }),
      });

      const revisedItems = [
        { metric_code: 'height', value_numeric: 120 },
      ];

      const { reviewService } = await import('../api/services');
      const result = await reviewService.approve('task-1', revisedItems);

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/review-tasks/task-1/approve`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ revised_items: revisedItems }),
        })
      );
      expect(result.status).toBe('approved');
    });

    it('409 状态冲突', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: () => Promise.resolve({ detail: 'Task already processed' }),
      });

      const { reviewService } = await import('../api/services');
      
      await expect(reviewService.approve('task-1', [])).rejects.toThrow('Task already processed');
    });
  });

  describe('reviewService.reject', () => {
    it('成功退回', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'review_rejected' }),
      });

      const { reviewService } = await import('../api/services');
      const result = await reviewService.reject('task-1');

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/review-tasks/task-1/reject`,
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.status).toBe('review_rejected');
    });
  });
});

describe('API 服务层 - TrendService', () => {
  const BASE_URL = 'http://10.0.2.2:8000';

  describe('trendService.getTrends', () => {
    it('成功获取趋势数据', async () => {
      const mockTrend = {
        metric: 'height',
        series: [
          { date: '2026-03-29', value: 120, side: null },
          { date: '2024-09-21', value: 115, side: null },
        ],
        reference_range: '110-130cm',
        alert_status: 'normal',
        comparison: { current: 120, previous: 115, delta: 5 },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTrend),
      });

      const { trendService } = await import('../api/services');
      const result = await trendService.getTrends('mem-1', 'height', '3m');

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/members/mem-1/trends?metric=height&range=3m`,
        expect.any(Object)
      );
      expect(result.series).toHaveLength(2);
      const comp = result.comparison as { current: number; previous: number; delta: number };
      expect(comp.current).toBe(120);
    });

    it('空数据', async () => {
      const mockTrend = {
        metric: 'height',
        series: [],
        reference_range: null,
        alert_status: 'normal',
        comparison: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTrend),
      });

      const { trendService } = await import('../api/services');
      const result = await trendService.getTrends('mem-1', 'height');

      expect(result.series).toHaveLength(0);
    });
  });

  describe('trendService.getVisionDashboard', () => {
    it('成功获取视力仪表盘', async () => {
      const mockDashboard = {
        member_id: 'mem-1',
        member_type: 'child',
        baseline_age_months: 96,
        axial_length: {
          series: [],
          reference_range: null,
          alert_status: 'normal',
          growth_rate: null,
          comparison: null,
        },
        vision_acuity: {
          series: [],
          reference_range: '0.8-1.2',
          alert_status: 'normal',
          growth_rate: null,
          comparison: null,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockDashboard),
      });

      const { trendService } = await import('../api/services');
      const result = await trendService.getVisionDashboard('mem-1');

      expect(result.member_type).toBe('child');
      expect(result.axial_length).toBeDefined();
    });
  });

  describe('trendService.getGrowthDashboard', () => {
    it('成功获取生长发育仪表盘', async () => {
      const mockDashboard = {
        member_id: 'mem-1',
        member_type: 'child',
        height: {
          series: [],
          reference_range: null,
          alert_status: 'normal',
          growth_rate: 5,
          comparison: null,
        },
        weight: {
          series: [],
          reference_range: null,
          alert_status: 'normal',
          growth_rate: 2,
          comparison: null,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockDashboard),
      });

      const { trendService } = await import('../api/services');
      const result = await trendService.getGrowthDashboard('mem-1');

      expect(result.member_type).toBe('child');
      expect(result.height.growth_rate).toBe(5);
    });
  });
});

describe('API 服务层 - DocumentService', () => {
  const BASE_URL = 'http://10.0.2.2:8000';

  describe('documentService.upload', () => {
    it('成功上传文件', async () => {
      const mockResponse = {
        document_id: 'doc-1',
        status: 'uploaded',
        file_url: 'minio://health-records/test.jpg',
        desensitized_url: 'minio://health-records/test_safe.jpg',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const { documentService } = await import('../api/services');
      const file = { uri: 'file://test.jpg', type: 'image/jpeg', name: 'test.jpg' };
      const result: any = await documentService.upload(file, 'mem-1');

      expect(result.document_id).toBe('doc-1');
      expect(result.status).toBe('uploaded');
    });

    it('上传失败 - 413 文件过大', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 413,
        json: () => Promise.resolve({ detail: 'File too large' }),
      });

      const { documentService } = await import('../api/services');
      const file = { uri: 'file://big.jpg', type: 'image/jpeg', name: 'big.jpg' };
      
      await expect(documentService.upload(file, 'mem-1')).rejects.toThrow('Upload failed: 413');
    });

    it('上传失败 - 网络错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { documentService } = await import('../api/services');
      const file = { uri: 'file://test.jpg', type: 'image/jpeg', name: 'test.jpg' };
      
      await expect(documentService.upload(file, 'mem-1')).rejects.toThrow('Network error');
    });
  });
});

describe('API 服务层 - ExamService', () => {
  const BASE_URL = 'http://10.0.2.2:8000';

  describe('examService.getRecord', () => {
    it('成功获取检查记录', async () => {
      const mockRecord = {
        id: 'rec-1',
        member_id: 'mem-1',
        exam_date: '2026-03-29',
        institution_name: 'XX医院',
        observations: [
          { id: 'obs-1', exam_record_id: 'rec-1', metric_code: 'height', value_numeric: 120, value_text: null, unit: 'cm', side: null, recorded_at: '2026-03-29T10:00:00Z' },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockRecord),
      });

      const { examService } = await import('../api/services');
      const result = await examService.getRecord('rec-1');

      expect(result.exam_date).toBe('2026-03-29');
      expect(result.observations).toHaveLength(1);
    });

    it('404 记录不存在', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Record not found' }),
      });

      const { examService } = await import('../api/services');
      
      await expect(examService.getRecord('999')).rejects.toThrow('Record not found');
    });
  });

  describe('examService.deleteExamRecord', () => {
    it('成功删除', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      const { examService } = await import('../api/services');
      const result = await examService.deleteExamRecord('rec-1');

      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/records/exam-records/rec-1`,
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('examService.createManualExam', () => {
    it('成功创建手动检查记录', async () => {
      const mockResponse = { id: 'rec-1', status: 'persisted' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const { examService } = await import('../api/services');
      const result = await examService.createManualExam('mem-1', {
        exam_date: '2026-04-05',
        institution_name: '市第一医院',
        observations: [
          { metric_code: 'height', value_numeric: 125.5, unit: 'cm', side: null },
          { metric_code: 'axial_length', value_numeric: 23.5, unit: 'mm', side: 'left' },
          { metric_code: 'axial_length', value_numeric: 23.3, unit: 'mm', side: 'right' },
        ],
      });

      expect(result.id).toBe('rec-1');
      expect(result.status).toBe('persisted');
      expect(mockFetch).toHaveBeenCalledWith(
        `${BASE_URL}/api/v1/records/members/mem-1/manual-exams`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            exam_date: '2026-04-05',
            institution_name: '市第一医院',
            observations: [
              { metric_code: 'height', value_numeric: 125.5, unit: 'cm', side: null },
              { metric_code: 'axial_length', value_numeric: 23.5, unit: 'mm', side: 'left' },
              { metric_code: 'axial_length', value_numeric: 23.3, unit: 'mm', side: 'right' },
            ],
          }),
        })
      );
    });

    it('422 数值超出区间校验', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: () => Promise.resolve({ detail: '身高数值 500 超出常规合理范围 (30-250cm)' }),
      });

      const { examService } = await import('../api/services');
      
      await expect(examService.createManualExam('mem-1', {
        exam_date: '2026-04-05',
        observations: [
          { metric_code: 'height', value_numeric: 500, unit: 'cm', side: null },
        ],
      })).rejects.toThrow('身高数值 500 超出常规合理范围 (30-250cm)');
    });
  });
});

describe('API 错误处理', () => {
  describe('网络超时', () => {
    it('fetch 超时抛出错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('timeout of 30000ms exceeded'));

      const { memberService } = await import('../api/services');
      
      await expect(memberService.list()).rejects.toThrow('timeout of 30000ms exceeded');
    });
  });

  describe('DNS 解析失败', () => {
    it('ENOTFOUND 错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('getaddrinfo ENOTFOUND localhost'));

      const { memberService } = await import('../api/services');
      
      await expect(memberService.list()).rejects.toThrow('ENOTFOUND');
    });
  });

  describe('连接被拒绝', () => {
    it('ECONNREFUSED 错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('connect ECONNREFUSED 127.0.0.1:8000'));

      const { memberService } = await import('../api/services');
      
      await expect(memberService.list()).rejects.toThrow('ECONNREFUSED');
    });
  });

  describe('CORS 错误', () => {
    it('CORS 错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('CORS error: Origin not allowed'));

      const { memberService } = await import('../api/services');
      
      await expect(memberService.list()).rejects.toThrow('CORS');
    });
  });
});
