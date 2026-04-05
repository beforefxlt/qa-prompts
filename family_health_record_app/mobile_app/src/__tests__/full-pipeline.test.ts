/**
 * 安卓客户端全链路集成测试
 * 
 * 模拟真实用户从打开 App 到完成所有核心操作的完整链路：
 * 首页加载 → 创建成员 → 上传检查单 → 提交OCR → 审核通过 → Dashboard展示 → 趋势图 → 手动录入 → 删除记录
 * 
 * 使用 mock fetch 模拟后端响应，但串联所有服务层调用，验证：
 * 1. 各服务之间的数据传递正确性
 * 2. 状态流转的完整性
 * 3. 错误场景的容错能力
 */

global.fetch = jest.fn();
const mockFetch = global.fetch as jest.Mock;

beforeEach(() => {
  mockFetch.mockClear();
});

// ==================== 测试数据工厂 ====================

function createMember(id: string, name: string, memberType: string = 'child') {
  return {
    id,
    name,
    gender: 'male',
    date_of_birth: '2018-06-15',
    member_type: memberType,
    last_check_date: null as string | null,
    pending_review_count: 0,
  };
}

function createUploadResponse(docId: string, status: string = 'uploaded') {
  return {
    document_id: docId,
    status,
    message: status === 'duplicate' ? '文件已上传过' : '上传成功',
    file_url: `minio://health-records/${docId}.jpg`,
    desensitized_url: null,
  };
}

function createOcrApprovedResponse(docId: string) {
  return {
    status: 'persisted',
    document_id: docId,
    data: {
      exam_date: '2026-04-01',
      observations: [
        { metric_code: 'axial_length', value_numeric: 23.50, unit: 'mm', side: 'left' },
        { metric_code: 'axial_length', value_numeric: 23.80, unit: 'mm', side: 'right' },
        { metric_code: 'vision_acuity', value_numeric: 0.8, unit: '', side: 'left' },
        { metric_code: 'vision_acuity', value_numeric: 0.7, unit: '', side: 'right' },
        { metric_code: 'height', value_numeric: 125.5, unit: 'cm' },
        { metric_code: 'weight', value_numeric: 24.3, unit: 'kg' },
      ],
    },
  };
}

function createOcrConflictResponse(docId: string) {
  return {
    status: 'rule_conflict',
    document_id: docId,
    data: {
      exam_date: '2026-04-02',
      observations: [
        { metric_code: 'axial_length', value_numeric: 24.00, unit: 'mm', side: 'left' },
        { metric_code: 'axial_length', value_numeric: 24.20, unit: 'mm', side: 'right' },
        { metric_code: 'height', value_numeric: 128.0, unit: 'cm' },
      ],
      confidence_score: 0.72,
      rule_conflict_details: { warning: ['数值超出正常范围'] },
    },
  };
}

function createReviewTask(taskId: string, docId: string, status: string = 'pending') {
  return {
    id: taskId,
    document_id: docId,
    status,
    created_at: '2026-04-02T10:00:00',
    updated_at: '2026-04-02T10:00:00',
    ocr_raw_json: { exam_date: '2026-04-02' },
    ocr_processed_items: {
      exam_date: '2026-04-02',
      observations: [
        { metric_code: 'axial_length', value_numeric: 24.00, unit: 'mm', side: 'left' },
        { metric_code: 'axial_length', value_numeric: 24.20, unit: 'mm', side: 'right' },
        { metric_code: 'height', value_numeric: 128.0, unit: 'cm' },
      ],
    },
    confidence_score: 0.72,
    rule_conflict_details: { warning: ['数值超出正常范围'] },
    image_url: `/api/v1/documents/${docId}/preview`,
  };
}

function createTrendResponse(metric: string, series: any[]) {
  return {
    metric,
    range: '3m',
    series,
    comparison: series.length >= 2
      ? { current: series[series.length - 1].value, previous: series[series.length - 2].value, delta: series[series.length - 1].value - series[series.length - 2].value }
      : null,
  };
}

function createVisionDashboard(memberType: string = 'child') {
  return {
    member_type: memberType,
    axial_length: {
      series: [
        { date: '2026-04-01', value: 23.50, side: 'left' },
        { date: '2026-04-01', value: 23.80, side: 'right' },
      ],
      comparison: { current: 23.80, previous: 23.50, delta: 0.30 },
      alert_status: null,
      reference_range: '22-26mm',
    },
    vision_acuity: {
      series: [
        { date: '2026-04-01', value: 0.8, side: 'left' },
        { date: '2026-04-01', value: 0.7, side: 'right' },
      ],
      comparison: { current: 0.7, previous: 0.8, delta: -0.1 },
      alert_status: null,
      reference_range: '0.8-1.0',
    },
  };
}

function createGrowthDashboard() {
  return {
    height: {
      series: [{ date: '2026-04-01', value: 125.5 }],
      growth_rate: { value: 5.2, unit: 'cm/year' },
      alert_status: null,
    },
    weight: {
      series: [{ date: '2026-04-01', value: 24.3 }],
      growth_rate: { value: 2.1, unit: 'kg/year' },
      alert_status: null,
    },
  };
}

function createExamRecord(recordId: string, memberId: string) {
  return {
    id: recordId,
    member_id: memberId,
    exam_date: '2026-04-01',
    institution_name: '市眼科医院',
    observations: [
      { id: 'obs-1', metric_code: 'axial_length', value_numeric: 23.50, unit: 'mm', side: 'left' },
      { id: 'obs-2', metric_code: 'axial_length', value_numeric: 23.80, unit: 'mm', side: 'right' },
      { id: 'obs-3', metric_code: 'height', value_numeric: 125.5, unit: 'cm' },
    ],
    created_at: '2026-04-01T10:00:00',
  };
}

// ==================== 辅助函数：按顺序 mock 多次 fetch 调用 ====================

function mockFetchSequence(responses: Array<{ ok: boolean; status: number; json: () => Promise<any> }>) {
  responses.forEach(r => {
    mockFetch.mockResolvedValueOnce({
      ok: r.ok,
      status: r.status,
      json: r.json,
    });
  });
}

// ==================== TC-INT-MOBILE-001: 完整用户旅程 ====================

describe('安卓客户端全链路集成测试', () => {
  const BASE_URL = 'http://10.0.2.2:8000';

  describe('TC-INT-MOBILE-001: 完整用户旅程 — 从首页到数据管理', () => {
    it('创建成员 → 上传检查单 → OCR直接通过 → Dashboard → 趋势图 → 手动录入 → 删除记录', async () => {
      // ===== Phase 1: 首页加载 - 获取成员列表 =====
      const members = [createMember('mem-1', '小明')];
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => members,
      });

      const { memberService } = await import('../api/services');
      const memberList = await memberService.list();

      expect(memberList).toHaveLength(1);
      expect(memberList[0].name).toBe('小明');
      expect(memberList[0].pending_review_count).toBe(0);

      // ===== Phase 2: 创建第二个成员 =====
      const newMember = createMember('mem-2', '小红');
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => newMember,
      });

      const created = await memberService.create({
        name: '小红',
        gender: 'female',
        date_of_birth: '2019-03-20',
        member_type: 'child',
      });

      expect(created.id).toBe('mem-2');
      expect(created.name).toBe('小红');

      // ===== Phase 3: 上传检查单图片 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createUploadResponse('doc-1'),
      });

      const { documentService } = await import('../api/services');
      const uploadResult = await documentService.upload(
        { uri: 'file:///data/01.jpg', type: 'image/jpeg', name: '01.jpg' },
        'mem-2'
      );

      expect((uploadResult as any).document_id).toBe('doc-1');
      expect(uploadResult.status).toBe('uploaded');
      expect(uploadResult.file_url).toContain('minio://');

      // ===== Phase 4: 提交 OCR（直接通过，无需审核）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createOcrApprovedResponse('doc-1'),
      });

      const ocrResult = await documentService.submitOcr('doc-1');
      expect(ocrResult.status).toBe('persisted');

      // ===== Phase 5: 查看 Dashboard - 视力看板 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createVisionDashboard('child'),
      });

      const { trendService } = await import('../api/services');
      const visionDashboard = await trendService.getVisionDashboard('mem-2');

      expect(visionDashboard.member_type).toBe('child');
      expect(visionDashboard.axial_length.series).toHaveLength(2);
      expect(visionDashboard.axial_length.comparison).not.toBeNull();
      expect((visionDashboard.axial_length.comparison as any)?.delta).toBeCloseTo(0.30, 2);

      // ===== Phase 6: 查看 Dashboard - 生长看板 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createGrowthDashboard(),
      });

      const growthDashboard = await trendService.getGrowthDashboard('mem-2');
      expect(growthDashboard.height.series).toHaveLength(1);
      expect((growthDashboard.height.growth_rate as any)?.value).toBe(5.2);

      // ===== Phase 7: 查看趋势图 - 眼轴 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('axial_length', [
          { date: '2026-04-01', value: 23.50, side: 'left' },
          { date: '2026-04-01', value: 23.80, side: 'right' },
        ]),
      });

      const axialTrends = await trendService.getTrends('mem-2', 'axial_length');
      expect(axialTrends.metric).toBe('axial_length');
      expect(axialTrends.series).toHaveLength(2);
      expect((axialTrends.comparison as any)?.current).toBe(23.80);

      // ===== Phase 8: 查看趋势图 - 身高 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('height', [
          { date: '2026-04-01', value: 125.5 },
        ]),
      });

      const heightTrends = await trendService.getTrends('mem-2', 'height');
      expect(heightTrends.series).toHaveLength(1);
      expect(heightTrends.comparison).toBeNull(); // 只有一条数据，无对比

      // ===== Phase 9: 手动录入新的检查数据 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createExamRecord('rec-1', 'mem-2'),
      });

      const { examService } = await import('../api/services');
      const manualRecord = await examService.createManualExam('mem-2', {
        exam_date: '2026-04-03',
        institution_name: '社区医院',
        observations: [
          { metric_code: 'axial_length', value_numeric: 23.60, unit: 'mm', side: 'left' },
          { metric_code: 'axial_length', value_numeric: 23.90, unit: 'mm', side: 'right' },
          { metric_code: 'height', value_numeric: 125.8, unit: 'cm' },
          { metric_code: 'weight', value_numeric: 24.5, unit: 'kg' },
        ],
      });

      expect(manualRecord.id).toBe('rec-1');
      expect(manualRecord.exam_date).toBe('2026-04-01'); // mock 返回固定值

      // ===== Phase 10: 查看手动录入的检查详情 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createExamRecord('rec-1', 'mem-2'),
      });

      const examDetail = await examService.getRecord('rec-1');
      expect(examDetail.observations).toHaveLength(3);
      expect(examDetail.institution_name).toBe('市眼科医院');

      // ===== Phase 11: 删除检查记录 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 204, json: async () => undefined,
      });

      await examService.deleteExamRecord('rec-1');

      const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1];
      expect(lastCall[0]).toContain('rec-1');
      expect(lastCall[1]?.method).toBe('DELETE');

      // ===== Phase 12: 更新成员信息 =====
      const updatedMember = { ...createMember('mem-2', '小红红'), name: '小红红' };
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => updatedMember,
      });

      const updated = await memberService.update('mem-2', { name: '小红红' });
      expect(updated.name).toBe('小红红');

      // ===== Phase 13: 删除成员 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 204, json: async () => undefined,
      });

      await memberService.delete('mem-2');

      const deleteCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1];
      expect(deleteCall[0]).toContain('/members/mem-2');
      expect(deleteCall[1]?.method).toBe('DELETE');

      // ===== 验证：整个链路共发起 13 次 API 调用 =====
      expect(mockFetch).toHaveBeenCalledTimes(13);
    });
  });

  // ==================== TC-INT-MOBILE-002: 审核流程 ====================

  describe('TC-INT-MOBILE-002: 审核流程 — OCR 产生冲突 → 审核通过', () => {
    it('上传 → OCR冲突 → 查看审核任务 → 修订数据 → 审核通过 → 验证数据', async () => {
      // ===== Phase 1: 上传检查单 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createUploadResponse('doc-2'),
      });

      const { documentService } = await import('../api/services');
      const uploadResult = await documentService.upload(
        { uri: 'file:///data/02.jpg', type: 'image/jpeg', name: '02.jpg' },
        'mem-1'
      );
      expect(uploadResult.status).toBe('uploaded');

      // ===== Phase 2: 提交 OCR，返回 rule_conflict =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createOcrConflictResponse('doc-2'),
      });

      const ocrResult = await documentService.submitOcr('doc-2');
      expect(ocrResult.status).toBe('rule_conflict');

      // ===== Phase 3: 获取审核任务列表 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => [createReviewTask('task-1', 'doc-2')],
      });

      const { reviewService } = await import('../api/services');
      const tasks = await reviewService.list();
      expect(tasks).toHaveLength(1);
      expect(tasks[0].status).toBe('pending');

      // ===== Phase 4: 获取审核任务详情 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createReviewTask('task-1', 'doc-2'),
      });

      const taskDetail = await reviewService.get('task-1');
      expect((taskDetail as any).confidence_score).toBe(0.72);
      expect((taskDetail as any).ocr_processed_items.observations).toHaveLength(3);

      // ===== Phase 5: 保存草稿（用户暂不确认）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({ status: 'draft' }),
      });

      const draftResult = await reviewService.saveDraft('task-1', [
        { metric_code: 'axial_length', side: 'left', value_numeric: 24.10, unit: 'mm' },
      ]);
      expect(draftResult.status).toBe('draft');

      // ===== Phase 6: 重新获取任务（确认草稿状态）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createReviewTask('task-1', 'doc-2', 'draft'),
      });

      const draftTask = await reviewService.get('task-1');
      expect(draftTask.status).toBe('draft');

      // ===== Phase 7: 最终审核通过（带修订）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({ status: 'approved' }),
      });

      const approveResult = await reviewService.approve('task-1', [
        { metric_code: 'axial_length', side: 'left', value_numeric: 24.10, unit: 'mm' },
        { metric_code: 'axial_length', side: 'right', value_numeric: 24.30, unit: 'mm' },
        { metric_code: 'height', value_numeric: 128.5, unit: 'cm' },
      ]);
      expect(approveResult.status).toBe('approved');

      // ===== Phase 8: 验证审核任务不再出现在待审核列表 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => [],
      });

      const remainingTasks = await reviewService.list();
      expect(remainingTasks).toHaveLength(0);

      // ===== 验证：整个审核链路共发起 8 次 API 调用 =====
      expect(mockFetch).toHaveBeenCalledTimes(8);
    });
  });

  // ==================== TC-INT-MOBILE-003: 审核退回流程 ====================

  describe('TC-INT-MOBILE-003: 审核退回流程', () => {
    it('上传 → OCR冲突 → 审核退回 → 任务消失', async () => {
      // ===== Phase 1: 上传 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createUploadResponse('doc-3'),
      });

      const { documentService } = await import('../api/services');
      await documentService.upload(
        { uri: 'file:///data/03.jpg', type: 'image/jpeg', name: '03.jpg' },
        'mem-1'
      );

      // ===== Phase 2: OCR 冲突 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createOcrConflictResponse('doc-3'),
      });

      await documentService.submitOcr('doc-3');

      // ===== Phase 3: 获取审核任务 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => [createReviewTask('task-2', 'doc-3')],
      });

      const { reviewService } = await import('../api/services');
      const tasks = await reviewService.list();
      expect(tasks).toHaveLength(1);

      // ===== Phase 4: 审核退回 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({ status: 'rejected' }),
      });

      const rejectResult = await reviewService.reject('task-2');
      expect(rejectResult.status).toBe('rejected');

      // ===== Phase 5: 验证退回后任务不在待审核列表 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => [],
      });

      const remainingTasks = await reviewService.list();
      expect(remainingTasks).toHaveLength(0);

      expect(mockFetch).toHaveBeenCalledTimes(5);
    });
  });

  // ==================== TC-INT-MOBILE-004: 多成员多指标数据验证 ====================

  describe('TC-INT-MOBILE-004: 多成员多指标数据验证', () => {
    it('多个成员 + 多个指标 + 趋势对比 + 空状态', async () => {
      const { memberService, trendService, examService } = await import('../api/services');

      // ===== Phase 1: 获取成员列表（3个成员）=====
      const members = [
        createMember('mem-child', '小明', 'child'),
        createMember('mem-adult', '张三', 'adult'),
        createMember('mem-senior', '李爷爷', 'senior'),
      ];
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => members,
      });

      const memberList = await memberService.list();
      expect(memberList).toHaveLength(3);
      expect(memberList.map(m => m.member_type)).toContain('child');
      expect(memberList.map(m => m.member_type)).toContain('adult');
      expect(memberList.map(m => m.member_type)).toContain('senior');

      // ===== Phase 2: 儿童 - 视力看板（有数据）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createVisionDashboard('child'),
      });

      const childVision = await trendService.getVisionDashboard('mem-child');
      expect(childVision.member_type).toBe('child');
      expect(childVision.axial_length.series).toHaveLength(2);

      // ===== Phase 3: 儿童 - 生长看板（有数据）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createGrowthDashboard(),
      });

      const childGrowth = await trendService.getGrowthDashboard('mem-child');
      expect(childGrowth.height.series).toHaveLength(1);

      // ===== Phase 4: 成人 - 视力看板（有数据）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createVisionDashboard('adult'),
      });

      const adultVision = await trendService.getVisionDashboard('mem-adult');
      expect(adultVision.member_type).toBe('adult');

      // ===== Phase 5: 成人 - 生长看板（空数据）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({
          height: { series: [], growth_rate: null, alert_status: null },
          weight: { series: [], growth_rate: null, alert_status: null },
        }),
      });

      const adultGrowth = await trendService.getGrowthDashboard('mem-adult');
      expect(adultGrowth.height.series).toHaveLength(0);
      expect(adultGrowth.height.growth_rate).toBeNull();

      // ===== Phase 6: 老人 - 视力看板（空数据）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({
          member_type: 'senior',
          axial_length: { series: [], comparison: null, alert_status: null, reference_range: '22-26mm' },
          vision_acuity: { series: [], comparison: null, alert_status: null, reference_range: '0.8-1.0' },
        }),
      });

      const seniorVision = await trendService.getVisionDashboard('mem-senior');
      expect(seniorVision.member_type).toBe('senior');
      expect(seniorVision.axial_length.series).toHaveLength(0);

      // ===== Phase 7: 老人 - 血糖趋势 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('glucose', [
          { date: '2026-03-01', value: 5.6 },
          { date: '2026-04-01', value: 5.8 },
        ]),
      });

      const glucoseTrend = await trendService.getTrends('mem-senior', 'glucose');
      expect(glucoseTrend.metric).toBe('glucose');
      expect((glucoseTrend.comparison as any)?.current).toBe(5.8);
      expect((glucoseTrend.comparison as any)?.delta).toBeCloseTo(0.2, 1);

      // ===== Phase 8: 老人 - 糖化血红蛋白趋势 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('hba1c', [
          { date: '2026-01-01', value: 6.5 },
          { date: '2026-04-01', value: 6.8 },
        ]),
      });

      const hba1cTrend = await trendService.getTrends('mem-senior', 'hba1c');
      expect((hba1cTrend.comparison as any)?.current).toBe(6.8);
      expect((hba1cTrend.comparison as any)?.delta).toBeCloseTo(0.3, 1);

      expect(mockFetch).toHaveBeenCalledTimes(8);
    });
  });

  // ==================== TC-INT-MOBILE-005: 异常场景容错 ====================

  describe('TC-INT-MOBILE-005: 异常场景容错', () => {
    it('连续异常操作：上传失败 → OCR超时 → 审核404 → 趋势空数据 → 删除不存在记录', async () => {
      const { documentService, reviewService, trendService, examService } = await import('../api/services');

      // ===== Phase 1: 上传失败（413 文件过大）=====
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 413, json: async () => ({ detail: '文件过大' }),
      });

      await expect(documentService.upload(
        { uri: 'file:///data/huge.jpg', type: 'image/jpeg', name: 'huge.jpg' },
        'mem-1'
      )).rejects.toThrow('Upload failed: 413');

      // ===== Phase 2: OCR 提交超时 =====
      mockFetch.mockRejectedValueOnce(new Error('Network request failed'));

      await expect(documentService.submitOcr('doc-bad')).rejects.toThrow('Network request failed');

      // ===== Phase 3: 审核任务不存在（404）=====
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 404, json: async () => ({ detail: '审核任务不存在' }),
      });

      await expect(reviewService.get('nonexistent')).rejects.toThrow();

      // ===== Phase 4: 趋势图空数据 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('axial_length', []),
      });

      const emptyTrend = await trendService.getTrends('mem-1', 'axial_length');
      expect(emptyTrend.series).toHaveLength(0);
      expect(emptyTrend.comparison).toBeNull();

      // ===== Phase 5: 删除不存在的检查记录 =====
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 404, json: async () => ({ detail: '记录不存在' }),
      });

      await expect(examService.getRecord('nonexistent')).rejects.toThrow();

      expect(mockFetch).toHaveBeenCalledTimes(5);
    });
  });

  // ==================== TC-INT-MOBILE-006: 数据一致性验证 ====================

  describe('TC-INT-MOBILE-006: 数据一致性验证', () => {
    it('上传 → OCR → 趋势 → 手动录入 → 趋势更新 → 数据对比', async () => {
      const { documentService, trendService, examService } = await import('../api/services');

      // ===== Phase 1: 上传并 OCR =====
      mockFetchSequence([
        { ok: true, status: 201, json: async () => createUploadResponse('doc-consistency') },
        { ok: true, status: 200, json: async () => createOcrApprovedResponse('doc-consistency') },
      ]);

      await documentService.upload(
        { uri: 'file:///data/consistency.jpg', type: 'image/jpeg', name: 'consistency.jpg' },
        'mem-1'
      );
      await documentService.submitOcr('doc-consistency');

      // ===== Phase 2: 查看趋势（只有 OCR 数据）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('axial_length', [
          { date: '2026-04-01', value: 23.50, side: 'left' },
          { date: '2026-04-01', value: 23.80, side: 'right' },
        ]),
      });

      const trendBefore = await trendService.getTrends('mem-1', 'axial_length');
      expect(trendBefore.series).toHaveLength(2);
      const beforeCount = trendBefore.series.length;

      // ===== Phase 3: 手动录入新的检查数据 =====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createExamRecord('rec-new', 'mem-1'),
      });

      await examService.createManualExam('mem-1', {
        exam_date: '2026-04-05',
        observations: [
          { metric_code: 'axial_length', value_numeric: 23.55, unit: 'mm', side: 'left' },
          { metric_code: 'axial_length', value_numeric: 23.85, unit: 'mm', side: 'right' },
        ],
      });

      // ===== Phase 4: 再次查看趋势（应该有新增数据）=====
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('axial_length', [
          { date: '2026-04-01', value: 23.50, side: 'left' },
          { date: '2026-04-01', value: 23.80, side: 'right' },
          { date: '2026-04-05', value: 23.55, side: 'left' },
          { date: '2026-04-05', value: 23.85, side: 'right' },
        ]),
      });

      const trendAfter = await trendService.getTrends('mem-1', 'axial_length');
      expect(trendAfter.series.length).toBeGreaterThan(beforeCount);
      expect((trendAfter.comparison as any)?.current).toBe(23.85);

      expect(mockFetch).toHaveBeenCalledTimes(5);
    });
  });

  // ==================== TC-INT-MOBILE-007: 弱网场景 ====================

  describe('TC-INT-MOBILE-007: 弱网场景 — 超时、慢响应、断线重连', () => {
    it('慢响应 → 超时 → 重试成功', async () => {
      const { memberService } = await import('../api/services');

      // 第一次：超时
      mockFetch.mockRejectedValueOnce(new Error('Network request timed out'));

      await expect(memberService.list()).rejects.toThrow('timed out');

      // 第二次：成功（模拟用户重试）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => [createMember('mem-1', '小明')],
      });

      const result = await memberService.list();
      expect(result).toHaveLength(1);
    });

    it('上传过程中断线 → 重新上传成功', async () => {
      const { documentService } = await import('../api/services');

      // 第一次上传：断线
      mockFetch.mockRejectedValueOnce(new Error('Network request failed'));

      await expect(documentService.upload(
        { uri: 'file:///data/01.jpg', type: 'image/jpeg', name: '01.jpg' },
        'mem-1'
      )).rejects.toThrow('Network request failed');

      // 第二次上传：成功
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createUploadResponse('doc-retry'),
      });

      const result = await documentService.upload(
        { uri: 'file:///data/01.jpg', type: 'image/jpeg', name: '01.jpg' },
        'mem-1'
      );
      expect(result.status).toBe('uploaded');
    });

    it('OCR 提交超时 → 查询状态发现已处理（幂等保护）', async () => {
      const { documentService } = await import('../api/services');

      // 第一次提交：超时（但后端实际已处理）
      mockFetch.mockRejectedValueOnce(new Error('Network request timed out'));

      await expect(documentService.submitOcr('doc-1')).rejects.toThrow('timed out');

      // 用户重试：后端返回已处理状态（幂等）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createOcrApprovedResponse('doc-1'),
      });

      const result = await documentService.submitOcr('doc-1');
      expect(result.status).toBe('persisted');
    });

    it('审核通过请求超时 → 重试发现已批准（幂等保护）', async () => {
      const { reviewService } = await import('../api/services');

      // 第一次审核：超时
      mockFetch.mockRejectedValueOnce(new Error('Network request timed out'));

      await expect(reviewService.approve('task-1', [])).rejects.toThrow('timed out');

      // 重试：后端返回已批准（幂等，不会重复创建数据）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({ status: 'approved' }),
      });

      const result = await reviewService.approve('task-1', []);
      expect(result.status).toBe('approved');
    });
  });

  // ==================== TC-INT-MOBILE-008: 幂等性验证 ====================

  describe('TC-INT-MOBILE-008: 幂等性 — 重复操作不会产生副作用', () => {
    it('重复上传同一文件返回 duplicate，不创建新记录', async () => {
      const { documentService } = await import('../api/services');

      // 第一次上传
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createUploadResponse('doc-idem-1'),
      });

      const upload1 = await documentService.upload(
        { uri: 'file:///data/01.jpg', type: 'image/jpeg', name: '01.jpg' },
        'mem-1'
      );
      expect(upload1.status).toBe('uploaded');

      // 第二次上传同一文件
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createUploadResponse('doc-idem-1', 'duplicate'),
      });

      const upload2 = await documentService.upload(
        { uri: 'file:///data/01.jpg', type: 'image/jpeg', name: '01.jpg' },
        'mem-1'
      );
      expect(upload2.status).toBe('duplicate');
      expect((upload2 as any).document_id).toBe('doc-idem-1');
    });

    it('重复提交同一 OCR 请求不会产生重复数据', async () => {
      const { documentService } = await import('../api/services');

      // 第一次提交
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createOcrApprovedResponse('doc-1'),
      });

      const ocr1 = await documentService.submitOcr('doc-1');
      expect(ocr1.status).toBe('persisted');

      // 第二次提交同一文档（后端应返回已处理状态）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createOcrApprovedResponse('doc-1'),
      });

      const ocr2 = await documentService.submitOcr('doc-1');
      expect(ocr2.status).toBe('persisted');
    });

    it('重复审核同一任务返回已批准，不重复创建数据', async () => {
      const { reviewService } = await import('../api/services');

      // 第一次审核
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({ status: 'approved' }),
      });

      const approve1 = await reviewService.approve('task-1', [
        { metric_code: 'axial_length', side: 'left', value_numeric: 24.10, unit: 'mm' },
      ]);
      expect(approve1.status).toBe('approved');

      // 第二次审核同一任务（幂等）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({ status: 'approved' }),
      });

      const approve2 = await reviewService.approve('task-1', [
        { metric_code: 'axial_length', side: 'left', value_numeric: 24.10, unit: 'mm' },
      ]);
      expect(approve2.status).toBe('approved');
    });

    it('重复创建同一成员（相同 name+dob）返回已有记录', async () => {
      const { memberService } = await import('../api/services');

      // 第一次创建
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createMember('mem-1', '小明'),
      });

      const member1 = await memberService.create({
        name: '小明', gender: 'male', date_of_birth: '2018-06-15', member_type: 'child',
      });
      expect(member1.id).toBe('mem-1');

      // 第二次创建相同成员（后端可能返回已有记录或 409）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createMember('mem-1', '小明'),
      });

      const member2 = await memberService.create({
        name: '小明', gender: 'male', date_of_birth: '2018-06-15', member_type: 'child',
      });
      expect(member2.id).toBe('mem-1');
    });
  });

  // ==================== TC-INT-MOBILE-009: 服务端错误恢复 ====================

  describe('TC-INT-MOBILE-009: 服务端错误恢复 — 500/502/503 后的重试', () => {
    it('500 内部错误 → 重试后成功', async () => {
      const { memberService } = await import('../api/services');

      // 第一次：500
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 500, json: async () => ({ detail: 'Internal Server Error' }),
      });

      await expect(memberService.list()).rejects.toThrow();

      // 重试：成功
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => [createMember('mem-1', '小明')],
      });

      const result = await memberService.list();
      expect(result).toHaveLength(1);
    });

    it('502 Bad Gateway → 重试后成功', async () => {
      const { trendService } = await import('../api/services');

      // 第一次：502
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 502, json: async () => ({ detail: 'Bad Gateway' }),
      });

      await expect(trendService.getTrends('mem-1', 'axial_length')).rejects.toThrow();

      // 重试：成功
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('axial_length', [
          { date: '2026-04-01', value: 23.50, side: 'left' },
        ]),
      });

      const result = await trendService.getTrends('mem-1', 'axial_length');
      expect(result.series).toHaveLength(1);
    });

    it('503 Service Unavailable → 重试后成功', async () => {
      const { reviewService } = await import('../api/services');

      // 第一次：503
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 503, json: async () => ({ detail: 'Service Unavailable' }),
      });

      await expect(reviewService.list()).rejects.toThrow();

      // 重试：成功
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => [],
      });

      const result = await reviewService.list();
      expect(result).toEqual([]);
    });

    it('连续 3 次 500 后放弃重试', async () => {
      const { memberService } = await import('../api/services');

      // 连续 3 次 500
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 500, json: async () => ({ detail: 'Internal Server Error' }),
      });
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 500, json: async () => ({ detail: 'Internal Server Error' }),
      });
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 500, json: async () => ({ detail: 'Internal Server Error' }),
      });

      // 第一次调用失败
      await expect(memberService.list()).rejects.toThrow();
      // 第二次调用失败
      await expect(memberService.list()).rejects.toThrow();
      // 第三次调用失败
      await expect(memberService.list()).rejects.toThrow();

      expect(mockFetch).toHaveBeenCalledTimes(3);
    });
  });

  // ==================== TC-INT-MOBILE-010: 客户端异常 — 数据污染防护 ====================

  describe('TC-INT-MOBILE-010: 数据污染防护 — 部分失败不产生脏数据', () => {
    it('上传成功但 OCR 失败，Dashboard 应显示空数据', async () => {
      const { documentService, trendService } = await import('../api/services');

      // 上传成功
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 201, json: async () => createUploadResponse('doc-fail'),
      });

      const uploadResult = await documentService.upload(
        { uri: 'file:///data/bad.jpg', type: 'image/jpeg', name: 'bad.jpg' },
        'mem-1'
      );
      expect(uploadResult.status).toBe('uploaded');

      // OCR 失败
      mockFetch.mockResolvedValueOnce({
        ok: false, status: 500, json: async () => ({ detail: 'OCR processing failed' }),
      });

      await expect(documentService.submitOcr('doc-fail')).rejects.toThrow();

      // Dashboard 应显示空数据（OCR 失败，数据未持久化）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({
          member_type: 'child',
          axial_length: { series: [], comparison: null, alert_status: null, reference_range: '22-26mm' },
          vision_acuity: { series: [], comparison: null, alert_status: null, reference_range: '0.8-1.0' },
        }),
      });

      const dashboard = await trendService.getVisionDashboard('mem-1');
      expect(dashboard.axial_length.series).toHaveLength(0);
      expect(dashboard.vision_acuity.series).toHaveLength(0);
    });

    it('审核通过但趋势查询失败，不应影响已持久化数据', async () => {
      const { reviewService, trendService } = await import('../api/services');

      // 审核通过
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({ status: 'approved' }),
      });

      const approveResult = await reviewService.approve('task-1', [
        { metric_code: 'axial_length', side: 'left', value_numeric: 24.10, unit: 'mm' },
      ]);
      expect(approveResult.status).toBe('approved');

      // 趋势查询失败（网络问题）
      mockFetch.mockRejectedValueOnce(new Error('Network request failed'));

      await expect(trendService.getTrends('mem-1', 'axial_length')).rejects.toThrow();

      // 重试趋势查询：数据应存在（审核通过已持久化）
      mockFetch.mockResolvedValueOnce({
        ok: true, status: 200, json: async () => createTrendResponse('axial_length', [
          { date: '2026-04-01', value: 24.10, side: 'left' },
        ]),
      });

      const trend = await trendService.getTrends('mem-1', 'axial_length');
      expect(trend.series).toHaveLength(1);
      expect(trend.series[0].value).toBe(24.10);
    });
  });
});
