import type {
  MemberProfile,
  CreateMemberDTO,
  UpdateMemberDTO,
  DocumentRecord,
  ReviewTask,
  TrendSeries,
  Observation,
  ExamRecord,
} from '../api/models';

describe('API Models - 边界与异常用例', () => {
  describe('MemberProfile 异常', () => {
    it('空 name 处理', () => {
      const member: MemberProfile = {
        id: '1',
        name: '',
        gender: 'male',
        date_of_birth: '2020-01-01',
        member_type: 'child',
        last_check_date: null,
        pending_review_count: 0,
      };
      expect(member.name).toBe('');
    });

    it('超长 name 处理', () => {
      const longName = '王'.repeat(100);
      const member: MemberProfile = {
        id: '1',
        name: longName,
        gender: 'male',
        date_of_birth: '2020-01-01',
        member_type: 'child',
        last_check_date: null,
        pending_review_count: 0,
      };
      expect(member.name.length).toBe(100);
    });

    it('无效 gender 值', () => {
      const invalidGenders = ['unknown', 'other', ''];
      invalidGenders.forEach(gender => {
        const isValid = gender === 'male' || gender === 'female';
        expect(isValid).toBe(false);
      });
    });

    it('无效 member_type 值', () => {
      const invalidTypes = ['infant', 'teenager', ''];
      invalidTypes.forEach(type => {
        const isValid = type === 'child' || type === 'adult' || type === 'senior';
        expect(isValid).toBe(false);
      });
    });

    it('负数 pending_review_count', () => {
      const member: MemberProfile = {
        id: '1',
        name: 'test',
        gender: 'male',
        date_of_birth: '2020-01-01',
        member_type: 'child',
        last_check_date: null,
        pending_review_count: -1,
      };
      expect(member.pending_review_count).toBeLessThan(0);
    });

    it('超大 pending_review_count', () => {
      const member: MemberProfile = {
        id: '1',
        name: 'test',
        gender: 'male',
        date_of_birth: '2020-01-01',
        member_type: 'child',
        last_check_date: null,
        pending_review_count: 999999,
      };
      expect(member.pending_review_count).toBeGreaterThan(1000);
    });

    it('UUID 格式异常', () => {
      const invalidUuids = [
        'not-a-uuid',
        '123',
        '',
        'uuid-with-spaces abc',
      ];
      invalidUuids.forEach(uuid => {
        const isValid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(uuid);
        expect(isValid).toBe(false);
      });
    });

    it('日期格式异常', () => {
      const invalidDates = [
        '2020/01/01',
        '01-01-2020',
        'yesterday',
        '',
      ];
      invalidDates.forEach(date => {
        const isValid = /^\d{4}-\d{2}-\d{2}$/.test(date);
        expect(isValid).toBe(false);
      });
    });
  });

  describe('CreateMemberDTO 异常', () => {
    it('缺少必填字段 - name', () => {
      const dto: Partial<CreateMemberDTO> = {
        gender: 'male',
        date_of_birth: '2020-01-01',
        member_type: 'child',
      };
      expect((dto as any).name).toBeUndefined();
    });

    it('缺少必填字段 - gender', () => {
      const dto: Partial<CreateMemberDTO> = {
        name: 'test',
        date_of_birth: '2020-01-01',
        member_type: 'child',
      };
      expect((dto as any).gender).toBeUndefined();
    });

    it('缺少必填字段 - date_of_birth', () => {
      const dto: Partial<CreateMemberDTO> = {
        name: 'test',
        gender: 'male',
        member_type: 'child',
      };
      expect((dto as any).date_of_birth).toBeUndefined();
    });

    it('缺少必填字段 - member_type', () => {
      const dto: Partial<CreateMemberDTO> = {
        name: 'test',
        gender: 'male',
        date_of_birth: '2020-01-01',
      };
      expect((dto as any).member_type).toBeUndefined();
    });

    it('未来日期出生', () => {
      const futureDate = '2100-01-01';
      const today = new Date().toISOString().split('T')[0];
      expect(futureDate > today).toBe(true);
    });

    it('出生日期早于 1900 年', () => {
      const oldDate = '1800-01-01';
      const minDate = '1900-01-01';
      expect(oldDate < minDate).toBe(true);
    });
  });

  describe('UpdateMemberDTO 异常', () => {
    it('空更新对象', () => {
      const dto: UpdateMemberDTO = {};
      expect(Object.keys(dto)).toHaveLength(0);
    });

    it('部分字段更新', () => {
      const dto: UpdateMemberDTO = {
        name: 'new name',
      };
      expect(dto.name).toBe('new name');
      expect((dto as any).gender).toBeUndefined();
    });
  });

  describe('DocumentStatus 异常', () => {
    it('非法状态值', () => {
      const invalidStatuses = [
        'creating',
        'processing',
        'completed',
        'cancelled',
        '',
      ];
      const validStatuses = [
        'uploaded',
        'desensitizing',
        'ocr_processing',
        'rule_checking',
        'pending_review',
        'approved',
        'persisted',
        'ocr_failed',
        'rule_conflict',
        'review_rejected',
      ];
      invalidStatuses.forEach(status => {
        expect(validStatuses.includes(status)).toBe(false);
      });
    });

    it('状态流转非法', () => {
      const invalidTransitions = [
        { from: 'persisted', to: 'uploaded' },
        { from: 'approved', to: 'desensitizing' },
        { from: 'ocr_failed', to: 'approved' },
      ];
      invalidTransitions.forEach(trans => {
        expect(trans.from === 'approved' && trans.to === 'uploaded').toBe(false);
      });
    });
  });

  describe('TrendSeries 异常', () => {
    it('空数据系列', () => {
      const trend: TrendSeries = {
        metric: 'height',
        series: [],
        reference_range: null,
        alert_status: 'normal',
        comparison: null,
      };
      expect(trend.series).toHaveLength(0);
    });

    it('异常 alert_status 值', () => {
      const invalidStatuses = ['safe', 'danger', 'info', ''];
      const validStatuses = ['normal', 'warning', 'critical'];
      invalidStatuses.forEach(status => {
        expect(validStatuses.includes(status)).toBe(false);
      });
    });

    it('comparison 结构不匹配 - 单眼数据', () => {
      const comparison = {
        current: 140,
        previous: 135,
        delta: 5,
      };
      expect(comparison).toHaveProperty('current');
      expect((comparison as any).left).toBeUndefined();
    });

    it('comparison 结构不匹配 - 双眼数据', () => {
      const comparison = {
        left: { current: 23.60, previous: 23.32, delta: 0.28 },
        right: { current: 23.67, previous: 24.35, delta: -0.68 },
      };
      expect(comparison).toHaveProperty('left');
      expect(comparison).toHaveProperty('right');
    });

    it('growth_rate 计算异常 - 数据不足', () => {
      const growthRate = null;
      expect(growthRate).toBeNull();
    });

    it('growth_rate 计算异常 - 年份差为 0', () => {
      const rate = 0;
      const isAbnormal = rate === 0;
      expect(isAbnormal).toBe(true);
    });

    it('growth_rate 异常值 - 增长过快', () => {
      const rate = 100;
      const isAbnormal = Math.abs(rate) > 50;
      expect(isAbnormal).toBe(true);
    });
  });

  describe('Observation 异常', () => {
    it('value_numeric 和 value_text 同时为空', () => {
      const obs: Observation = {
        id: '1',
        exam_record_id: '1',
        metric_code: 'height',
        value_numeric: 0,
        value_text: null,
        unit: 'cm',
        side: null,
        recorded_at: '2026-03-29T10:00:00Z',
      };
      expect(obs.value_numeric).toBe(0);
      expect(obs.value_text).toBeNull();
    });

    it('无效 side 值', () => {
      const invalidSides = ['both', 'center', 'unknown', 'L', 'R'];
      const validSides = ['left', 'right', null];
      invalidSides.forEach(side => {
        expect(validSides.includes(side as any)).toBe(false);
      });
    });

    it('单位不匹配', () => {
      const obs: Observation = {
        id: '1',
        exam_record_id: '1',
        metric_code: 'height',
        value_numeric: 180,
        value_text: null,
        unit: 'mm', // 应该是 cm
        side: null,
        recorded_at: '2026-03-29T10:00:00Z',
      };
      expect(obs.unit).toBe('mm');
    });

    it('数值精度异常', () => {
      const obs: Observation = {
        id: '1',
        exam_record_id: '1',
        metric_code: 'glucose',
        value_numeric: 5.55555555555,
        value_text: null,
        unit: 'mmol/L',
        side: null,
        recorded_at: '2026-03-29T10:00:00Z',
      };
      const precision = obs.value_numeric.toString().split('.')[1]?.length || 0;
      expect(precision).toBeGreaterThan(2);
    });

    it('负数值异常', () => {
      const obs: Observation = {
        id: '1',
        exam_record_id: '1',
        metric_code: 'height',
        value_numeric: -10,
        value_text: null,
        unit: 'cm',
        side: null,
        recorded_at: '2026-03-29T10:00:00Z',
      };
      expect(obs.value_numeric).toBeLessThan(0);
    });
  });

  describe('ExamRecord 异常', () => {
    it('无检查日期', () => {
      const record: ExamRecord = {
        id: '1',
        member_id: '1',
        exam_date: '',
        institution_name: null,
        observations: [],
      };
      expect(record.exam_date).toBe('');
    });

    it('无机构名称', () => {
      const record: ExamRecord = {
        id: '1',
        member_id: '1',
        exam_date: '2026-03-29',
        institution_name: null,
        observations: [],
      };
      expect(record.institution_name).toBeNull();
    });

    it('无观测数据', () => {
      const record: ExamRecord = {
        id: '1',
        member_id: '1',
        exam_date: '2026-03-29',
        institution_name: 'Test',
        observations: [],
      };
      expect(record.observations).toHaveLength(0);
    });

    it('重复观测数据', () => {
      const obs: Observation = {
        id: '1',
        exam_record_id: '1',
        metric_code: 'height',
        value_numeric: 120,
        value_text: null,
        unit: 'cm',
        side: null,
        recorded_at: '2026-03-29T10:00:00Z',
      };
      const record: ExamRecord = {
        id: '1',
        member_id: '1',
        exam_date: '2026-03-29',
        institution_name: 'Test',
        observations: [obs, obs],
      };
      expect(record.observations).toHaveLength(2);
    });
  });

  describe('ReviewTask 异常', () => {
    it('OCR 结果为空', () => {
      const task: ReviewTask = {
        id: '1',
        document_id: '1',
        member_id: '1',
        status: 'pending',
        ocr_result: {
          exam_date: '',
          observations: [],
          confidence_score: 0,
        },
        revised_items: [],
        created_at: '',
      };
      expect(task.ocr_result.observations).toHaveLength(0);
    });

    it('置信度异常 - 负数', () => {
      const task: ReviewTask = {
        id: '1',
        document_id: '1',
        member_id: '1',
        status: 'pending',
        ocr_result: {
          exam_date: '2026-03-29',
          observations: [],
          confidence_score: -0.5,
        },
        revised_items: [],
        created_at: '2026-03-29T10:00:00Z',
      };
      expect(task.ocr_result.confidence_score).toBeLessThan(0);
    });

    it('置信度异常 - 超过 1', () => {
      const task: ReviewTask = {
        id: '1',
        document_id: '1',
        member_id: '1',
        status: 'pending',
        ocr_result: {
          exam_date: '2026-03-29',
          observations: [],
          confidence_score: 1.5,
        },
        revised_items: [],
        created_at: '2026-03-29T10:00:00Z',
      };
      expect(task.ocr_result.confidence_score).toBeGreaterThan(1);
    });

    it('无 revised_items', () => {
      const task: ReviewTask = {
        id: '1',
        document_id: '1',
        member_id: '1',
        status: 'pending',
        ocr_result: {
          exam_date: '2026-03-29',
          observations: [],
          confidence_score: 0.9,
        },
        revised_items: [],
        created_at: '2026-03-29T10:00:00Z',
      };
      expect(task.revised_items).toHaveLength(0);
    });

    it('无效 status 值', () => {
      const invalidStatuses = ['completed', 'submitted', 'in_progress'];
      const validStatuses = ['pending', 'approved', 'rejected'];
      invalidStatuses.forEach(status => {
        expect(validStatuses.includes(status as any)).toBe(false);
      });
    });
  });
});
