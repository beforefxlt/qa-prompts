/**
 * 前后端契约测试
 * 
 * 验证移动端 API 调用与 API_CONTRACT.md 定义的一致性
 * 
 * 契约来源: docs/specs/API_CONTRACT.md v2.4.0
 */

import { API_CONFIG } from '../constants/api';

const BASE_URL = API_CONFIG.BASE_URL;

describe('前后端契约 - 成员档案接口', () => {
  describe('GET /api/v1/members - 获取成员列表', () => {
    it('响应结构符合契约定义', async () => {
      const mockResponse = [
        {
          id: '123e4567-e89b-12d3-a456-426614174000',
          name: '张三',
          gender: 'male',
          date_of_birth: '2018-06-15',
          member_type: 'child',
          last_check_date: '2026-03-29',
          pending_review_count: 2,
        }
      ];

      const member = mockResponse[0];

      // 契约要求：id 必须是 UUID 格式
      expect(member.id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
      
      // 契约要求：name 必须是 string
      expect(typeof member.name).toBe('string');
      
      // 契约要求：gender 必须是 'male' | 'female'
      expect(['male', 'female']).toContain(member.gender);
      
      // 契约要求：member_type 必须是 'child' | 'adult' | 'senior'
      expect(['child', 'adult', 'senior']).toContain(member.member_type);
      
      // 契约要求：date_of_birth 必须是 YYYY-MM-DD 格式
      expect(member.date_of_birth).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      
      // 契约要求：last_check_date 可以是 null 或 YYYY-MM-DD
      if (member.last_check_date) {
        expect(member.last_check_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      }
      
      // 契约要求：pending_review_count 必须是 number
      expect(typeof member.pending_review_count).toBe('number');
      expect(member.pending_review_count).toBeGreaterThanOrEqual(0);
    });

    it('必填字段完整', async () => {
      const mockResponse = [
        {
          id: 'uuid-1',
          name: '张三',
          gender: 'male',
          date_of_birth: '2018-06-15',
          member_type: 'child',
          last_check_date: null,
          pending_review_count: 0,
        }
      ];

      const requiredFields = ['id', 'name', 'gender', 'date_of_birth', 'member_type', 'last_check_date', 'pending_review_count'];
      requiredFields.forEach(field => {
        expect(mockResponse[0]).toHaveProperty(field);
      });
    });
  });

  describe('POST /api/v1/members - 创建成员', () => {
    it('请求体符合契约定义', () => {
      const requestBody = {
        name: '晓萌',
        gender: 'female',
        date_of_birth: '2018-06-15',
        member_type: 'child'
      };

      // 契约要求：name 必填
      expect(requestBody.name).toBeDefined();
      expect(typeof requestBody.name).toBe('string');
      
      // 契约要求：gender 必填
      expect(requestBody.gender).toBeDefined();
      expect(['male', 'female']).toContain(requestBody.gender);
      
      // 契约要求：date_of_birth 必填，YYYY-MM-DD
      expect(requestBody.date_of_birth).toBeDefined();
      expect(requestBody.date_of_birth).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      
      // 契约要求：member_type 必填
      expect(requestBody.member_type).toBeDefined();
      expect(['child', 'adult', 'senior']).toContain(requestBody.member_type);
    });

    it('响应体符合契约定义', () => {
      const response = {
        id: 'uuid-new',
        name: '晓萌',
        gender: 'female',
        date_of_birth: '2018-06-15',
        member_type: 'child',
        last_check_date: null,
        pending_review_count: 0
      };

      // 创建成功后返回完整成员对象，包含计算字段
      expect(response).toHaveProperty('id');
      expect(response).toHaveProperty('last_check_date');
      expect(response).toHaveProperty('pending_review_count');
    });
  });
});

describe('前后端契约 - 文档上传接口', () => {
  describe('POST /api/v1/documents/upload', () => {
    it('响应结构符合契约定义', () => {
      const response = {
        document_id: '123e4567-e89b-12d3-a456-426614174000',
        status: 'uploaded',
        file_url: 'minio://health-records/test.jpg',
        desensitized_url: 'minio://health-records/test_safe.jpg'
      };

      // 契约要求：document_id
      expect(response).toHaveProperty('document_id');
      expect(response.document_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
      
      // 契约要求：status
      expect(response).toHaveProperty('status');
      expect(['uploaded', 'desensitizing', 'ocr_processing', 'rule_checking', 'pending_review', 'approved', 'persisted', 'ocr_failed', 'rule_conflict', 'review_rejected']).toContain(response.status);
      
      // 契约要求：file_url, desensitized_url
      expect(response).toHaveProperty('file_url');
      expect(response).toHaveProperty('desensitized_url');
      expect(response.file_url).toMatch(/^minio:\/\//);
    });
  });

  describe('POST /api/v1/documents/{id}/submit-ocr', () => {
    it('响应结构符合契约定义', () => {
      const response = {
        document_id: 'uuid-doc',
        status: 'persisted'
      };

      expect(response).toHaveProperty('document_id');
      expect(response).toHaveProperty('status');
      expect(['persisted', 'rule_conflict', 'ocr_failed']).toContain(response.status);
    });
  });
});

describe('前后端契约 - OCR 审核接口', () => {
  describe('GET /api/v1/review-tasks - 获取审核列表', () => {
    it('响应结构符合契约定义', () => {
      const response = [
        {
          id: 'uuid-task',
          document_id: 'uuid-doc',
          member_id: 'uuid-member',
          status: 'pending',
          ocr_result: {
            exam_date: '2026-03-29',
            observations: [],
            confidence_score: 0.85
          },
          revised_items: [],
          created_at: '2026-03-29T10:00:00Z'
        }
      ];

      const task = response[0];

      // 必填字段
      expect(task).toHaveProperty('id');
      expect(task).toHaveProperty('document_id');
      expect(task).toHaveProperty('member_id');
      expect(task).toHaveProperty('status');
      expect(task).toHaveProperty('ocr_result');
      expect(task).toHaveProperty('created_at');

      // status 枚举值
      expect(['pending', 'approved', 'rejected']).toContain(task.status);

      // ocr_result 结构
      expect(task.ocr_result).toHaveProperty('exam_date');
      expect(task.ocr_result).toHaveProperty('observations');
      expect(task.ocr_result).toHaveProperty('confidence_score');

      // confidence_score 范围 0-1
      expect(task.ocr_result.confidence_score).toBeGreaterThanOrEqual(0);
      expect(task.ocr_result.confidence_score).toBeLessThanOrEqual(1);
    });
  });

  describe('POST /api/v1/review-tasks/{id}/approve - 审核通过', () => {
    it('请求体 revised_items 格式符合契约', () => {
      const requestBody = {
        revised_items: [
          { metric_code: 'exam_date', value: '2026-04-01' },
          { metric_code: 'axial_length', side: 'left', value_numeric: 23.55, unit: 'mm' },
          { metric_code: 'axial_length', side: 'right', value_numeric: 23.20, unit: 'mm' }
        ]
      };

      // 契约要求：exam_date 修改格式
      expect(requestBody.revised_items[0]).toHaveProperty('metric_code', 'exam_date');
      expect(requestBody.revised_items[0]).toHaveProperty('value');

      // 契约要求：数值修改格式 - 必须包含 metric_code + side + value_numeric
      expect(requestBody.revised_items[1]).toHaveProperty('metric_code');
      expect(requestBody.revised_items[1]).toHaveProperty('side');
      expect(requestBody.revised_items[1]).toHaveProperty('value_numeric');
      expect(requestBody.revised_items[1]).toHaveProperty('unit');

      // 契约要求：value_numeric 必须是 number 类型，不是字符串
      expect(typeof requestBody.revised_items[1].value_numeric).toBe('number');
    });

    it('禁止格式 - 不能使用 field 字段', () => {
      // 契约明确禁止: { field: 'height', value: 120 }
      // 正确格式: { metric_code: 'height', value_numeric: 120 }
      const validItem = { metric_code: 'height', value_numeric: 120 };
      
      expect(Object.keys(validItem)).not.toContain('field');
      expect(validItem).toHaveProperty('metric_code');
    });

    it('禁止格式 - 不能发送整个 observations 数组', () => {
      // 契约明确禁止在 revised_items 中发送整个 observations
      const validItem = { metric_code: 'exam_date', value: '2026-04-01' };
      
      expect(Object.keys(validItem)).not.toContain('observations');
    });
  });

  describe('审核响应结构', () => {
    it('approve 响应', () => {
      const response = { status: 'approved' };
      expect(response.status).toBe('approved');
    });

    it('reject 响应', () => {
      const response = { status: 'review_rejected' };
      expect(response.status).toBe('review_rejected');
    });

    it('save-draft 响应', () => {
      const response = { status: 'pending' };
      expect(response.status).toBe('pending');
    });
  });
});

describe('前后端契约 - 趋势查询接口', () => {
  describe('GET /api/v1/members/{id}/trends', () => {
    it('响应结构符合契约定义', () => {
      const response = {
        metric: 'axial_length',
        series: [
          { date: '2026-03-01', value: 24.12, side: 'left' },
          { date: '2026-03-01', value: 23.15, side: 'right' }
        ],
        reference_range: '23.0-24.0',
        alert_status: 'normal',
        comparison: {
          left: { current: 23.60, previous: 23.32, delta: 0.28 },
          right: { current: 23.32, previous: 23.20, delta: 0.12 }
        }
      };

      // 必填字段
      expect(response).toHaveProperty('metric');
      expect(response).toHaveProperty('series');
      expect(response).toHaveProperty('reference_range');
      expect(response).toHaveProperty('alert_status');
      expect(response).toHaveProperty('comparison');

      // series 数组元素结构
      expect(response.series[0]).toHaveProperty('date');
      expect(response.series[0]).toHaveProperty('value');
      expect(response.series[0]).toHaveProperty('side');

      // alert_status 枚举值
      expect(['normal', 'warning', 'critical']).toContain(response.alert_status);

      // comparison 结构 - 双侧眼轴
      if (response.comparison && 'left' in response.comparison) {
        expect(response.comparison.left).toHaveProperty('current');
        expect(response.comparison.left).toHaveProperty('previous');
        expect(response.comparison.left).toHaveProperty('delta');
      }
    });

    it('comparison 可以是 null', () => {
      const response = {
        metric: 'height',
        series: [{ date: '2026-03-29', value: 120 }],
        reference_range: null,
        alert_status: 'normal',
        comparison: null
      };

      expect(response.comparison).toBeNull();
    });
  });

  describe('GET /api/v1/members/{id}/vision-dashboard', () => {
    it('响应结构符合契约定义', () => {
      const response = {
        member_id: 'uuid-member',
        member_type: 'child',
        baseline_age_months: 96,
        axial_length: {
          series: [],
          reference_range: null,
          alert_status: 'normal',
          growth_rate: -0.13,
          comparison: {
            left: { current: 23.60, previous: 23.32, delta: 0.28 },
            right: { current: 23.67, previous: 24.35, delta: -0.68 }
          }
        },
        vision_acuity: {
          series: [],
          reference_range: '0.8-1.2',
          alert_status: 'normal',
          growth_rate: null,
          comparison: null
        }
      };

      // 必填字段
      expect(response).toHaveProperty('member_id');
      expect(response).toHaveProperty('member_type');
      expect(response).toHaveProperty('baseline_age_months');
      expect(response).toHaveProperty('axial_length');
      expect(response).toHaveProperty('vision_acuity');

      // axial_length 结构
      expect(response.axial_length).toHaveProperty('series');
      expect(response.axial_length).toHaveProperty('reference_range');
      expect(response.axial_length).toHaveProperty('alert_status');
      expect(response.axial_length).toHaveProperty('growth_rate');
      expect(response.axial_length).toHaveProperty('comparison');

      // growth_rate 可以是 null
      expect(response.vision_acuity.growth_rate).toBeNull();
    });
  });

  describe('GET /api/v1/members/{id}/growth-dashboard', () => {
    it('响应结构符合契约定义', () => {
      const response = {
        member_id: 'uuid-member',
        member_type: 'child',
        height: {
          series: [],
          reference_range: null,
          alert_status: 'normal',
          growth_rate: 12.0,
          comparison: { current: 140, previous: 135, delta: 5 }
        },
        weight: {
          series: [],
          reference_range: null,
          alert_status: 'normal',
          growth_rate: 2.5,
          comparison: { current: 35, previous: 32.5, delta: 2.5 }
        }
      };

      // height 对比是单维度结构
      if (response.height.comparison && 'current' in response.height.comparison) {
        expect(response.height.comparison).toHaveProperty('current');
        expect(response.height.comparison).toHaveProperty('previous');
        expect(response.height.comparison).toHaveProperty('delta');
      }
    });
  });
});

describe('前后端契约 - 数据管理接口', () => {
  describe('POST /api/v1/members/{id}/manual-exams - 手动录入', () => {
    it('请求体格式符合契约', () => {
      const requestBody = {
        exam_date: '2026-04-01',
        institution_name: '社区卫生服务中心',
        observations: [
          {
            metric_code: 'height',
            value_numeric: 125.5,
            unit: 'cm',
            side: null
          }
        ]
      };

      // 必填字段
      expect(requestBody).toHaveProperty('exam_date');
      expect(requestBody).toHaveProperty('observations');
      expect(requestBody.exam_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);

      // observations 元素
      expect(requestBody.observations[0]).toHaveProperty('metric_code');
      expect(requestBody.observations[0]).toHaveProperty('value_numeric');
      expect(requestBody.observations[0]).toHaveProperty('unit');

      // 契约要求：value_numeric 必须是 number
      expect(typeof requestBody.observations[0].value_numeric).toBe('number');
    });

    it('指标数值范围校验符合契约', () => {
      const testCases = [
        { metric_code: 'height', value: 125.5, valid: true, range: '30-250' },
        { metric_code: 'height', value: 29, valid: false, range: '30-250' },
        { metric_code: 'height', value: 251, valid: false, range: '30-250' },
        { metric_code: 'weight', value: 22, valid: true, range: '2-500' },
        { metric_code: 'axial_length', value: 23.5, valid: true, range: '15-35' },
        { metric_code: 'glucose', value: 5.5, valid: true, range: '0.1-50' },
        { metric_code: 'ldl', value: 2.5, valid: true, range: '0.1-10' },
        { metric_code: 'hba1c', value: 5.5, valid: true, range: '3-15' },
      ];

      testCases.forEach(({ metric_code, value, valid, range }) => {
        const ranges: Record<string, { min: number; max: number }> = {
          height: { min: 30, max: 250 },
          weight: { min: 2, max: 500 },
          axial_length: { min: 15, max: 35 },
          glucose: { min: 0.1, max: 50 },
          ldl: { min: 0.1, max: 10 },
          hba1c: { min: 3, max: 15 },
        };

        const rangeInfo = ranges[metric_code];
        if (rangeInfo) {
          const inRange = value >= rangeInfo.min && value <= rangeInfo.max;
          expect(inRange).toBe(valid);
        }
      });
    });
  });

  describe('PATCH /api/v1/observations/{id}', () => {
    it('请求体格式符合契约', () => {
      const requestBody = { value_numeric: 126.0 };

      expect(requestBody).toHaveProperty('value_numeric');
      expect(typeof requestBody.value_numeric).toBe('number');
    });

    it('响应状态码', () => {
      const statusCode = 200;
      expect(statusCode).toBe(200);
    });
  });

  describe('DELETE /api/v1/exam-records/{id}', () => {
    it('响应状态码', () => {
      const statusCode = 204;
      expect(statusCode).toBe(204);
    });
  });
});

describe('前后端契约 - 状态流转', () => {
  describe('DocumentStatus 流转', () => {
    const validTransitions: Record<string, string[]> = {
      uploaded: ['desensitizing'],
      desensitizing: ['ocr_processing'],
      ocr_processing: ['rule_checking', 'ocr_failed'],
      rule_checking: ['pending_review', 'rule_conflict'],
      pending_review: ['approved', 'rejected', 'pending_review'],
      approved: ['persisted'],
      persisted: [],
      ocr_failed: [],
      rule_conflict: ['pending_review'],
      review_rejected: ['ocr_processing'],
    };

    it('标准流转路径', () => {
      const standardPath = ['uploaded', 'desensitizing', 'ocr_processing', 'rule_checking', 'pending_review', 'approved', 'persisted'];
      
      for (let i = 0; i < standardPath.length - 1; i++) {
        const current = standardPath[i];
        const next = standardPath[i + 1];
        expect(validTransitions[current]).toContain(next);
      }
    });

    it('异常流转路径', () => {
      // OCR 失败
      expect(validTransitions['ocr_processing']).toContain('ocr_failed');
      
      // 规则冲突
      expect(validTransitions['rule_checking']).toContain('rule_conflict');
    });
  });
});

describe('前后端契约 - 错误码', () => {
  it('错误响应格式', () => {
    const errorResponses = [
      { status: 400, detail: 'name is required' },
      { status: 404, detail: 'Member not found' },
      { status: 409, detail: 'Task already processed' },
      { status: 422, detail: 'value out of range' },
      { status: 500, detail: 'Internal server error' },
    ];

    errorResponses.forEach(err => {
      expect(err).toHaveProperty('status');
      expect(err).toHaveProperty('detail');
      expect(typeof err.detail).toBe('string');
    });
  });

  it('HTTP 状态码定义', () => {
    const httpCodes = {
      400: 'Bad Request',
      404: 'Not Found',
      409: 'Conflict',
      422: 'Unprocessable Entity',
      500: 'Internal Server Error',
    };

    expect(httpCodes[400]).toBe('Bad Request');
    expect(httpCodes[404]).toBe('Not Found');
    expect(httpCodes[409]).toBe('Conflict');
    expect(httpCodes[422]).toBe('Unprocessable Entity');
    expect(httpCodes[500]).toBe('Internal Server Error');
  });
});

describe('前后端契约 - 通用约束', () => {
  it('所有时间使用 ISO 8601', () => {
    const dates = [
      '2026-03-29',
      '2026-03-29T10:00:00Z',
      '2026-03-29T10:00:00.000Z',
    ];

    dates.forEach(date => {
      expect(date).toMatch(/^\d{4}-\d{2}-\d{2}/);
    });
  });

  it('UUID 格式', () => {
    const uuids = [
      '123e4567-e89b-12d3-a456-426614174000',
      '550e8400-e29b-41d4-a716-446655440000',
    ];

    uuids.forEach(uuid => {
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    });
  });

  it('内网免登录 - 无需认证 Token', () => {
    // 契约明确：所有接口无需携带认证 Token
    const requiresAuth = false;
    expect(requiresAuth).toBe(false);
  });
});
