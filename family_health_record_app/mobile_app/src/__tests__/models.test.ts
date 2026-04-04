import type {
  MemberProfile,
  CreateMemberDTO,
  UpdateMemberDTO,
  DocumentRecord,
  DocumentStatus,
  ReviewTask,
  TrendSeries,
  TrendPoint,
  TrendComparison,
  VisionDashboard,
  GrowthDashboard,
  MetricData,
  Observation,
  ExamRecord,
} from '../api/models';

describe('API Models - MemberProfile', () => {
  it('should have correct shape for MemberProfile', () => {
    const member: MemberProfile = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      name: '张三',
      gender: 'male',
      date_of_birth: '2018-06-15',
      member_type: 'child',
      last_check_date: '2026-03-29',
      pending_review_count: 2,
    };

    expect(member.id).toBeDefined();
    expect(member.name).toBe('张三');
    expect(member.gender).toBe('male');
    expect(member.member_type).toBe('child');
    expect(member.pending_review_count).toBe(2);
  });

  it('should allow null last_check_date', () => {
    const member: MemberProfile = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      name: '李四',
      gender: 'female',
      date_of_birth: '1990-01-01',
      member_type: 'adult',
      last_check_date: null,
      pending_review_count: 0,
    };

    expect(member.last_check_date).toBeNull();
  });

  it('should validate member_type values', () => {
    const child: MemberProfile = {
      id: '1',
      name: 'child',
      gender: 'male',
      date_of_birth: '2020-01-01',
      member_type: 'child',
      last_check_date: null,
      pending_review_count: 0,
    };

    const adult: MemberProfile = { ...child, id: '2', member_type: 'adult' };
    const senior: MemberProfile = { ...child, id: '3', member_type: 'senior' };

    expect(child.member_type).toBe('child');
    expect(adult.member_type).toBe('adult');
    expect(senior.member_type).toBe('senior');
  });
});

describe('API Models - CreateMemberDTO', () => {
  it('should have correct shape for CreateMemberDTO', () => {
    const dto: CreateMemberDTO = {
      name: '王五',
      gender: 'male',
      date_of_birth: '2015-03-20',
      member_type: 'child',
    };

    expect(dto.name).toBe('王五');
    expect(dto.gender).toBe('male');
    expect(dto.date_of_birth).toBe('2015-03-20');
    expect(dto.member_type).toBe('child');
  });
});

describe('API Models - DocumentStatus', () => {
  it('should include all status values', () => {
    const statuses: DocumentStatus[] = [
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

    expect(statuses).toHaveLength(10);
  });
});

describe('API Models - TrendPoint', () => {
  it('should have correct shape for TrendPoint', () => {
    const point: TrendPoint = {
      date: '2026-03-29',
      value: 23.67,
      side: 'left',
    };

    expect(point.date).toBe('2026-03-29');
    expect(point.value).toBe(23.67);
    expect(point.side).toBe('left');
  });

  it('should allow string value for vision_acuity', () => {
    const point: TrendPoint = {
      date: '2026-03-29',
      value: '1.0',
      side: 'right',
    };

    expect(typeof point.value).toBe('string');
    expect(point.value).toBe('1.0');
  });

  it('should allow null side', () => {
    const point: TrendPoint = {
      date: '2026-03-29',
      value: 120,
      side: null,
    };

    expect(point.side).toBeNull();
  });
});

describe('API Models - TrendComparison', () => {
  it('should have single dimension comparison', () => {
    const comparison: TrendComparison = {
      current: 140,
      previous: 135,
      delta: 5,
    };

    expect(comparison).toHaveProperty('current', 140);
    expect(comparison).toHaveProperty('previous', 135);
    expect(comparison).toHaveProperty('delta', 5);
  });

  it('should have dual dimension comparison', () => {
    const comparison: TrendComparison = {
      left: { current: 23.60, previous: 23.32, delta: 0.28 },
      right: { current: 23.67, previous: 24.35, delta: -0.68 },
    };

    expect(comparison).toHaveProperty('left');
    expect(comparison).toHaveProperty('right');
    expect((comparison as any).left.delta).toBe(0.28);
  });

  it('should allow null comparison', () => {
    const comparison: TrendComparison = null;
    expect(comparison).toBeNull();
  });
});

describe('API Models - MetricData', () => {
  it('should have correct shape for MetricData', () => {
    const metricData: MetricData = {
      series: [
        { date: '2026-03-29', value: 23.67, side: 'left' },
        { date: '2024-09-21', value: 23.32, side: 'left' },
      ],
      reference_range: '21-25mm',
      alert_status: 'normal',
      growth_rate: -0.13,
      comparison: {
        left: { current: 23.60, previous: 23.32, delta: 0.28 },
        right: { current: 23.67, previous: 24.35, delta: -0.68 },
      },
    };

    expect(metricData.series).toHaveLength(2);
    expect(metricData.reference_range).toBe('21-25mm');
    expect(metricData.alert_status).toBe('normal');
    expect(metricData.growth_rate).toBe(-0.13);
  });

  it('should allow null growth_rate', () => {
    const metricData: MetricData = {
      series: [],
      reference_range: null,
      alert_status: 'normal',
      growth_rate: null,
      comparison: null,
    };

    expect(metricData.growth_rate).toBeNull();
  });
});

describe('API Models - VisionDashboard', () => {
  it('should have correct shape for VisionDashboard', () => {
    const dashboard: VisionDashboard = {
      member_id: '123e4567-e89b-12d3-a456-426614174000',
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

    expect(dashboard.member_id).toBeDefined();
    expect(dashboard.axial_length).toBeDefined();
    expect(dashboard.vision_acuity).toBeDefined();
  });
});

describe('API Models - Observation', () => {
  it('should have correct shape for Observation', () => {
    const obs: Observation = {
      id: 'obs-001',
      exam_record_id: 'rec-001',
      metric_code: 'height',
      value_numeric: 120,
      value_text: null,
      unit: 'cm',
      side: null,
      recorded_at: '2026-03-29T10:00:00Z',
    };

    expect(obs.metric_code).toBe('height');
    expect(obs.value_numeric).toBe(120);
    expect(obs.unit).toBe('cm');
  });
});

describe('API Models - ExamRecord', () => {
  it('should have correct shape for ExamRecord', () => {
    const record: ExamRecord = {
      id: 'rec-001',
      member_id: 'mem-001',
      exam_date: '2026-03-29',
      institution_name: 'XX 眼科医院',
      observations: [
        {
          id: 'obs-001',
          exam_record_id: 'rec-001',
          metric_code: 'axial_length',
          value_numeric: 23.67,
          value_text: null,
          unit: 'mm',
          side: 'left',
          recorded_at: '2026-03-29T10:00:00Z',
        },
      ],
    };

    expect(record.exam_date).toBe('2026-03-29');
    expect(record.observations).toHaveLength(1);
  });
});
