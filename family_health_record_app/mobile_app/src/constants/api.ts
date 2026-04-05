const getEnv = (key: string, fallback: string) => {
  // @ts-ignore - Expo may inject env vars at build time
  return (typeof process !== 'undefined' && process.env && process.env[key]) || fallback;
};

export const API_CONFIG = {
  BASE_URL: getEnv('EXPO_PUBLIC_API_URL', 'http://10.0.2.2:8000'),
  API_PREFIX: '/api/v1',
  TIMEOUT: 30000,
  MINIO_BASE_URL: getEnv('EXPO_PUBLIC_MINIO_URL', 'http://10.0.2.2:9000/health-records/'),
} as const;

export const METRIC_RANGES = {
  height: { min: 30, max: 250, unit: 'cm' },
  weight: { min: 2, max: 500, unit: 'kg' },
  axial_length: { min: 15, max: 35, unit: 'mm' },
  vision_acuity: { min: 0, max: 3, unit: '' },
  glucose: { min: 0.1, max: 50, unit: 'mmol/L' },
  tc: { min: 0.1, max: 30, unit: 'mmol/L' },
  tg: { min: 0.1, max: 30, unit: 'mmol/L' },
  hdl: { min: 0.1, max: 10, unit: 'mmol/L' },
  ldl: { min: 0.1, max: 10, unit: 'mmol/L' },
  hemoglobin: { min: 30, max: 250, unit: 'g/L' },
  hba1c: { min: 3, max: 15, unit: '%' },
} as const;

export const METRIC_LABELS: Record<string, string> = {
  height: '身高',
  weight: '体重',
  axial_length: '眼轴',
  vision_acuity: '视力',
  glucose: '血糖',
  tc: '总胆固醇',
  tg: '甘油三酯',
  hdl: '高密度脂蛋白',
  ldl: '低密度脂蛋白',
  hemoglobin: '血红蛋白',
  hba1c: '糖化血红蛋白',
};

export const MEMBER_TYPE_LABELS: Record<string, string> = {
  child: '儿童',
  adult: '成人',
  senior: '老人',
};

export const GENDER_LABELS: Record<string, string> = {
  male: '男',
  female: '女',
};
