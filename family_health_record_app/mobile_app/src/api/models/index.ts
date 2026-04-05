export interface MemberProfile {
  id: string;
  name: string;
  gender: 'male' | 'female';
  date_of_birth: string;
  member_type: 'child' | 'adult' | 'senior';
  last_check_date: string | null;
  pending_review_count: number;
}

export interface CreateMemberDTO {
  name: string;
  gender: 'male' | 'female';
  date_of_birth: string;
  member_type: 'child' | 'adult' | 'senior';
}

export interface UpdateMemberDTO {
  name?: string;
  gender?: 'male' | 'female';
  date_of_birth?: string;
  member_type?: 'child' | 'adult' | 'senior';
}

export interface DocumentRecord {
  id: string;
  member_id: string;
  status: DocumentStatus;
  file_url: string;
  desensitized_url: string;
  uploaded_at: string;
}

export type DocumentStatus =
  | 'uploaded'
  | 'desensitizing'
  | 'ocr_processing'
  | 'rule_checking'
  | 'pending_review'
  | 'approved'
  | 'persisted'
  | 'ocr_failed'
  | 'rule_conflict'
  | 'review_rejected';

export interface OCRObservation {
  metric_code: string;
  value_numeric?: number;
  value?: string;
  unit?: string;
  side?: 'left' | 'right' | null;
  confidence?: number;
}

export interface RevisedItem {
  metric_code: string;
  side?: 'left' | 'right' | null;
  value?: string;
  value_numeric?: number;
  unit?: string;
}

export interface ReviewTask {
  id: string;
  document_id: string;
  member_id: string;
  status: 'pending' | 'approved' | 'rejected';
  ocr_result: {
    exam_date: string;
    observations: OCRObservation[];
    confidence_score: number;
  };
  revised_items: RevisedItem[];
  created_at: string;
}

export interface TrendPoint {
  date: string;
  value: number | string;
  side?: 'left' | 'right' | null;
}

export interface TrendComparisonSingle {
  current: number;
  previous: number;
  delta: number;
}

export interface TrendComparisonDual {
  left: { current: number; previous: number; delta: number };
  right: { current: number; previous: number; delta: number };
}

export type TrendComparison = TrendComparisonSingle | TrendComparisonDual | null;

export interface TrendSeries {
  metric: string;
  series: TrendPoint[];
  reference_range: string | null;
  alert_status: 'normal' | 'warning' | 'critical';
  comparison: TrendComparison;
  growth_rate?: number | null;
}

export interface MetricData {
  series: TrendPoint[];
  reference_range: string | null;
  alert_status: 'normal' | 'warning' | 'critical';
  growth_rate: number | null;
  comparison: TrendComparison;
}

export interface VisionDashboard {
  member_id: string;
  member_type: string;
  baseline_age_months: number;
  axial_length: MetricData;
  vision_acuity: MetricData;
}

export interface GrowthDashboard {
  member_id: string;
  member_type: string;
  height: MetricData;
  weight: MetricData;
}

export interface BloodDashboard {
  member_id: string;
  member_type: string;
  glucose: MetricData;
  tc: MetricData;
  tg: MetricData;
  hdl: MetricData;
  ldl: MetricData;
  hemoglobin: MetricData;
  hba1c: MetricData;
}

export interface Observation {
  id: string;
  exam_record_id: string;
  metric_code: string;
  value_numeric: number;
  value_text: string | null;
  unit: string;
  side: 'left' | 'right' | null;
  recorded_at: string;
}

export interface ExamRecord {
  id: string;
  member_id: string;
  exam_date: string;
  institution_name: string | null;
  observations: Observation[];
  status?: string;
}
