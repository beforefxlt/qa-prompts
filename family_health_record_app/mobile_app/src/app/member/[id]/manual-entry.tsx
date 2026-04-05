import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { useRouter, useLocalSearchParams } from 'expo-router';
import DateTimePicker from '@react-native-community/datetimepicker';
import { examService } from '../../../api/services';
import { METRIC_RANGES, METRIC_LABELS } from '../../../constants/api';

type ObservationRow = {
  id: string;
  metric_code: string;
  left_value: string;
  right_value: string;
  single_value: string;
};

const METRIC_OPTIONS = [
  { code: 'height', label: '身高', unit: 'cm', isEye: false },
  { code: 'weight', label: '体重', unit: 'kg', isEye: false },
  { code: 'axial_length', label: '眼轴', unit: 'mm', isEye: true },
  { code: 'vision_acuity', label: '视力', unit: '', isEye: true },
  { code: 'glucose', label: '血糖', unit: 'mmol/L', isEye: false },
  { code: 'ldl', label: '低密度脂蛋白', unit: 'mmol/L', isEye: false },
  { code: 'hemoglobin', label: '血红蛋白', unit: 'g/L', isEye: false },
  { code: 'hba1c', label: '糖化血红蛋白', unit: '%', isEye: false },
];

let rowIdCounter = 0;

export default function ManualEntryPage() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const [examDate, setExamDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [institution, setInstitution] = useState('');
  const [rows, setRows] = useState<ObservationRow[]>([
    { id: `row-${rowIdCounter++}`, metric_code: 'height', left_value: '', right_value: '', single_value: '' }
  ]);
  const [saving, setSaving] = useState(false);

  const addRow = () => {
    setRows([...rows, { id: `row-${rowIdCounter++}`, metric_code: 'height', left_value: '', right_value: '', single_value: '' }]);
  };

  const removeRow = (rowId: string) => {
    if (rows.length <= 1) {
      Alert.alert('提示', '至少保留一个指标');
      return;
    }
    setRows(rows.filter(r => r.id !== rowId));
  };

  const updateMetricCode = (rowId: string, newCode: string) => {
    setRows(rows.map(r =>
      r.id === rowId ? { ...r, metric_code: newCode, left_value: '', right_value: '', single_value: '' } : r
    ));
  };

  const handleSave = async () => {
    const observations: Array<{ metric_code: string; value_numeric: number; unit: string; side: string | null }> = [];

    for (const row of rows) {
      const metric = METRIC_OPTIONS.find(m => m.code === row.metric_code);
      if (!metric) continue;

      const range = METRIC_RANGES[row.metric_code as keyof typeof METRIC_RANGES];

      if (metric.isEye) {
        if (row.left_value.trim()) {
          const val = parseFloat(row.left_value);
          if (isNaN(val) || val <= 0) {
            Alert.alert('错误', `请填写有效的左眼${metric.label}数值`);
            return;
          }
          if (range && (val < range.min || val > range.max)) {
            Alert.alert('错误', `左眼${metric.label}数值 ${val} 超出合理范围 (${range.min}-${range.max})`);
            return;
          }
          observations.push({ metric_code: row.metric_code, value_numeric: val, unit: metric.unit, side: 'left' });
        }
        if (row.right_value.trim()) {
          const val = parseFloat(row.right_value);
          if (isNaN(val) || val <= 0) {
            Alert.alert('错误', `请填写有效的右眼${metric.label}数值`);
            return;
          }
          if (range && (val < range.min || val > range.max)) {
            Alert.alert('错误', `右眼${metric.label}数值 ${val} 超出合理范围 (${range.min}-${range.max})`);
            return;
          }
          observations.push({ metric_code: row.metric_code, value_numeric: val, unit: metric.unit, side: 'right' });
        }
      } else {
        if (!row.single_value.trim()) {
          Alert.alert('错误', `请填写${metric.label}数值`);
          return;
        }
        const val = parseFloat(row.single_value);
        if (isNaN(val) || val <= 0) {
          Alert.alert('错误', `请填写有效的${metric.label}数值`);
          return;
        }
        if (range && (val < range.min || val > range.max)) {
          Alert.alert('错误', `${metric.label}数值 ${val} 超出合理范围 (${range.min}-${range.max})`);
          return;
        }
        observations.push({ metric_code: row.metric_code, value_numeric: val, unit: metric.unit, side: null });
      }
    }

    if (observations.length === 0) {
      Alert.alert('错误', '请至少填写一个指标的数值');
      return;
    }

    setSaving(true);
    try {
      await examService.createManualExam(id!, {
        exam_date: examDate.toISOString().split('T')[0],
        institution_name: institution.trim() || undefined,
        observations,
      });
      Alert.alert('成功', '指标录入成功', [
        { text: '确定', onPress: () => router.back() }
      ]);
    } catch (error: any) {
      Alert.alert('错误', error.message || '录入失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (date: Date) => date.toISOString().split('T')[0];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.label}>检查日期</Text>
        <TouchableOpacity style={styles.dateInput} onPress={() => setShowDatePicker(true)}>
          <Text style={styles.dateText}>{formatDate(examDate)}</Text>
        </TouchableOpacity>
        {showDatePicker && (
          <DateTimePicker
            value={examDate}
            mode="date"
            display="default"
            onChange={(event, date) => {
              setShowDatePicker(false);
              if (date) setExamDate(date);
            }}
          />
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>机构名称（可选）</Text>
        <TextInput
          style={styles.input}
          value={institution}
          onChangeText={setInstitution}
          placeholder="例如：市第一眼科医院"
          placeholderTextColor="#999"
        />
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>指标数据</Text>
          <TouchableOpacity style={styles.addButton} onPress={addRow}>
            <Text style={styles.addButtonText}>+ 添加</Text>
          </TouchableOpacity>
        </View>

        {rows.map((row) => {
          const metric = METRIC_OPTIONS.find(m => m.code === row.metric_code);
          if (!metric) return null;

          return (
            <View key={row.id} style={styles.rowCard}>
              <View style={styles.rowHeader}>
                <View style={styles.metricSelector}>
                  {METRIC_OPTIONS.map(opt => (
                    <TouchableOpacity
                      key={opt.code}
                      style={[styles.metricChip, row.metric_code === opt.code && styles.metricChipActive]}
                      onPress={() => updateMetricCode(row.id, opt.code)}
                    >
                      <Text style={[styles.metricChipText, row.metric_code === opt.code && styles.metricChipTextActive]}>
                        {opt.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
                <TouchableOpacity style={styles.removeButton} onPress={() => removeRow(row.id)}>
                  <Text style={styles.removeButtonText}>×</Text>
                </TouchableOpacity>
              </View>

              {metric.isEye ? (
                <View style={styles.eyeRow}>
                  <View style={styles.eyeInput}>
                    <Text style={styles.eyeLabel}>左眼 {metric.unit ? `(${metric.unit})` : ''}</Text>
                    <TextInput
                      style={styles.numberInput}
                      value={row.left_value}
                      onChangeText={(text) => setRows(rows.map(r => r.id === row.id ? { ...r, left_value: text } : r))}
                      placeholder="—"
                      placeholderTextColor="#ccc"
                      keyboardType="decimal-pad"
                    />
                  </View>
                  <View style={styles.eyeInput}>
                    <Text style={styles.eyeLabel}>右眼 {metric.unit ? `(${metric.unit})` : ''}</Text>
                    <TextInput
                      style={styles.numberInput}
                      value={row.right_value}
                      onChangeText={(text) => setRows(rows.map(r => r.id === row.id ? { ...r, right_value: text } : r))}
                      placeholder="—"
                      placeholderTextColor="#ccc"
                      keyboardType="decimal-pad"
                    />
                  </View>
                </View>
              ) : (
                <View style={styles.singleInput}>
                  <Text style={styles.eyeLabel}>数值 ({metric.unit})</Text>
                  <TextInput
                    style={styles.numberInput}
                    value={row.single_value}
                    onChangeText={(text) => setRows(rows.map(r => r.id === row.id ? { ...r, single_value: text } : r))}
                    placeholder="请输入数值"
                    placeholderTextColor="#ccc"
                    keyboardType="decimal-pad"
                  />
                </View>
              )}
            </View>
          );
        })}
      </View>

      <TouchableOpacity
        style={[styles.saveButton, saving && styles.saveButtonDisabled]}
        onPress={handleSave}
        disabled={saving}
      >
        {saving ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.saveButtonText}>保存记录</Text>
        )}
      </TouchableOpacity>

      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 12,
  },
  label: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  dateInput: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
  },
  dateText: {
    fontSize: 16,
    color: '#333',
  },
  input: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  addButton: {
    backgroundColor: '#007AFF',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  rowCard: {
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e5e5e5',
  },
  rowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  metricSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    flex: 1,
  },
  metricChip: {
    backgroundColor: '#f0f0f0',
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  metricChipActive: {
    backgroundColor: '#007AFF',
  },
  metricChipText: {
    fontSize: 12,
    color: '#666',
  },
  metricChipTextActive: {
    color: '#fff',
  },
  removeButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#ff4444',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  removeButtonText: {
    color: '#fff',
    fontSize: 18,
    lineHeight: 20,
  },
  eyeRow: {
    flexDirection: 'row',
    gap: 12,
  },
  eyeInput: {
    flex: 1,
  },
  singleInput: {
    flex: 1,
  },
  eyeLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 6,
  },
  numberInput: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
    color: '#333',
    borderWidth: 1,
    borderColor: '#e5e5e5',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 8,
  },
  saveButtonDisabled: {
    backgroundColor: '#ccc',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});
