import { API_CONFIG, METRIC_RANGES, METRIC_LABELS, MEMBER_TYPE_LABELS, GENDER_LABELS } from '../constants/api';

describe('API Constants', () => {
  describe('API_CONFIG', () => {
    it('should have correct BASE_URL', () => {
      expect(API_CONFIG.BASE_URL).toBe('http://10.0.2.2:8000');
    });

    it('should have correct API_PREFIX', () => {
      expect(API_CONFIG.API_PREFIX).toBe('/api/v1');
    });

    it('should have TIMEOUT defined', () => {
      expect(API_CONFIG.TIMEOUT).toBe(30000);
    });
  });

  describe('METRIC_RANGES', () => {
    it('should have height range', () => {
      expect(METRIC_RANGES.height).toEqual({ min: 30, max: 250, unit: 'cm' });
    });

    it('should have weight range', () => {
      expect(METRIC_RANGES.weight).toEqual({ min: 2, max: 500, unit: 'kg' });
    });

    it('should have axial_length range', () => {
      expect(METRIC_RANGES.axial_length).toEqual({ min: 15, max: 35, unit: 'mm' });
    });

    it('should have glucose range', () => {
      expect(METRIC_RANGES.glucose).toEqual({ min: 0.1, max: 50, unit: 'mmol/L' });
    });

    it('should have all required metrics', () => {
      const requiredMetrics = ['height', 'weight', 'axial_length', 'glucose', 'ldl', 'hemoglobin', 'hba1c'];
      requiredMetrics.forEach(metric => {
        expect(METRIC_RANGES).toHaveProperty(metric);
      });
    });
  });

  describe('METRIC_LABELS', () => {
    it('should have height label', () => {
      expect(METRIC_LABELS.height).toBe('身高');
    });

    it('should have weight label', () => {
      expect(METRIC_LABELS.weight).toBe('体重');
    });

    it('should have axial_length label', () => {
      expect(METRIC_LABELS.axial_length).toBe('眼轴');
    });

    it('should have glucose label', () => {
      expect(METRIC_LABELS.glucose).toBe('血糖');
    });
  });

  describe('MEMBER_TYPE_LABELS', () => {
    it('should have child label', () => {
      expect(MEMBER_TYPE_LABELS.child).toBe('儿童');
    });

    it('should have adult label', () => {
      expect(MEMBER_TYPE_LABELS.adult).toBe('成人');
    });

    it('should have senior label', () => {
      expect(MEMBER_TYPE_LABELS.senior).toBe('老人');
    });
  });

  describe('GENDER_LABELS', () => {
    it('should have male label', () => {
      expect(GENDER_LABELS.male).toBe('男');
    });

    it('should have female label', () => {
      expect(GENDER_LABELS.female).toBe('女');
    });
  });

  describe('MINIO_BASE_URL', () => {
    it('BUG-REGRESSION #8: MINIO_BASE_URL 不应硬编码 localhost', () => {
      expect(API_CONFIG.MINIO_BASE_URL).not.toContain('localhost');
    });

    it('should use emulator address for development', () => {
      expect(API_CONFIG.MINIO_BASE_URL).toContain('10.0.2.2');
    });
  });
});
