import { View, Text, ScrollView, StyleSheet, Image } from 'react-native';
import { useState, useEffect } from 'react';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { examService } from '../../../../api/services';
import type { ExamRecord } from '../../../../api/models';
import { METRIC_LABELS } from '../../../../constants/api';

export default function RecordDetailPage() {
  const router = useRouter();
  const { id, recordId } = useLocalSearchParams<{ id: string; recordId: string }>();
  const [record, setRecord] = useState<ExamRecord | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecord();
  }, [id, recordId]);

  const loadRecord = async () => {
    try {
      const data = await examService.getRecord(recordId!);
      setRecord(data);
    } catch (error) {
      console.error('Failed to load record:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !record) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>加载中...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.dateText}>检查日期: {record.exam_date}</Text>
        {record.institution_name && (
          <Text style={styles.institutionText}>机构: {record.institution_name}</Text>
        )}
      </View>

      <View style={styles.imageSection}>
        <Text style={styles.sectionTitle}>检查单图片</Text>
        <View style={styles.imagePlaceholder}>
          <Text style={styles.placeholderText}>图片预览</Text>
        </View>
      </View>

      <View style={styles.observationsSection}>
        <Text style={styles.sectionTitle}>指标数据</Text>
        {record.observations.map((obs, index) => (
          <View key={index} style={styles.obsItem}>
            <Text style={styles.obsLabel}>
              {METRIC_LABELS[obs.metric_code] || obs.metric_code}
              {obs.side ? ` (${obs.side})` : ''}
            </Text>
            <Text style={styles.obsValue}>
              {obs.value_numeric ?? obs.value_text ?? 'N/A'}
              {obs.unit ? ` ${obs.unit}` : ''}
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 32,
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 16,
  },
  dateText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  institutionText: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  imageSection: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  imagePlaceholder: {
    width: '100%',
    height: 200,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 14,
    color: '#999',
  },
  observationsSection: {
    backgroundColor: '#fff',
    padding: 16,
  },
  obsItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  obsLabel: {
    fontSize: 14,
    color: '#666',
  },
  obsValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
});
