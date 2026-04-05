import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, Alert, Image } from 'react-native';
import { useState, useEffect } from 'react';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { reviewService } from '../../api/services';
import { resolveImageUrl } from '../../utils';
import { getServerHost, getMinioBaseUrl } from '../../config/serverConfig';
import type { ReviewTask, RevisedItem } from '../../api/models';
import { METRIC_LABELS } from '../../constants/api';

export default function ReviewDetailPage() {
  const router = useRouter();
  const { taskId } = useLocalSearchParams<{ taskId: string }>();
  const [task, setTask] = useState<ReviewTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [revisedItems, setRevisedItems] = useState<RevisedItem[]>([]);
  const [minioBaseUrl, setMinioBaseUrl] = useState('');

  useEffect(() => {
    loadTask();
    getServerHost().then(host => setMinioBaseUrl(getMinioBaseUrl(host)));
  }, [taskId]);

  const loadTask = async () => {
    try {
      const data = await reviewService.get(taskId!);
      setTask(data);
      setRevisedItems(data.revised_items || data.ocr_result?.observations?.map(o => ({
        metric_code: o.metric_code,
        side: o.side,
        value_numeric: o.value_numeric,
        value: o.value,
        unit: o.unit,
      })) || []);
    } catch (error) {
      Alert.alert('错误', '加载失败');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const updateItem = (index: number, field: string, value: any) => {
    const updated = [...revisedItems];
    updated[index] = { ...updated[index], [field]: value };
    setRevisedItems(updated);
  };

  const handleApprove = async () => {
    setSaving(true);
    try {
      await reviewService.approve(taskId!, revisedItems);
      Alert.alert('成功', '审核通过', [{ text: '确定', onPress: () => router.back() }]);
    } catch (error) {
      Alert.alert('错误', '审核失败');
    } finally {
      setSaving(false);
    }
  };

  const handleReject = async () => {
    Alert.alert('确认退回', '确定要退回重识别吗？', [
      { text: '取消', style: 'cancel' },
      {
        text: '退回',
        style: 'destructive',
        onPress: async () => {
          try {
            await reviewService.reject(taskId!);
            router.back();
          } catch (error) {
            Alert.alert('错误', '退回失败');
          }
        },
      },
    ]);
  };

  const handleSaveDraft = async () => {
    setSaving(true);
    try {
      await reviewService.saveDraft(taskId!, revisedItems);
      Alert.alert('成功', '草稿已保存', [{ text: '确定', onPress: () => router.back() }]);
    } catch (error) {
      Alert.alert('错误', '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const getConfidenceStyle = (score: number) => {
    if (score >= 0.8) return { bg: '#E8F5E9', text: '#2E7D32', label: '识别可信' };
    if (score >= 0.6) return { bg: '#FFF3CD', text: '#856404', label: '请核对关键字段' };
    return { bg: '#FFEBEE', text: '#C62828', label: '识别置信度低，请仔细核对' };
  };

  if (loading || !task) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>加载中...</Text>
      </View>
    );
  }

  const confidenceStyle = getConfidenceStyle(task.ocr_result?.confidence_score || 0);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.imageSection}>
        <Text style={styles.sectionTitle}>检查单图片</Text>
        {task.ocr_result?.observations?.[0] && (
          <Image
            source={{ uri: resolveImageUrl(
              task.ocr_result.observations[0].file_url,
              task.document_id,
              minioBaseUrl
            ) }}
            style={styles.image}
            resizeMode="contain"
          />
        )}
      </View>

      <View style={styles.formSection}>
        <Text style={styles.sectionTitle}>识别结果</Text>

        <View style={[styles.confidenceBadge, { backgroundColor: confidenceStyle.bg }]}>
          <Text style={[styles.confidenceText, { color: confidenceStyle.text }]}>
            {confidenceStyle.label} ({task.ocr_result?.confidence_score?.toFixed(2)})
          </Text>
        </View>

        {revisedItems.map((item, index) => (
          <View key={index} style={styles.fieldRow}>
            <Text style={styles.fieldLabel}>
              {METRIC_LABELS[item.metric_code] || item.metric_code}
              {item.side ? ` (${item.side})` : ''}
            </Text>
            <View style={styles.fieldInput}>
              <TextInput
                style={styles.input}
                value={item.value_numeric?.toString() || item.value || ''}
                onChangeText={(text) => {
                  const num = parseFloat(text);
                  updateItem(index, isNaN(num) ? 'value' : 'value_numeric', isNaN(num) ? text : num);
                }}
                keyboardType="numeric"
                placeholder="请输入"
              />
              {item.unit && <Text style={styles.unitText}>{item.unit}</Text>}
            </View>
          </View>
        ))}
      </View>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.rejectButton} onPress={handleReject}>
          <Text style={styles.rejectButtonText}>退回</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.draftButton} onPress={handleSaveDraft} disabled={saving}>
          <Text style={styles.draftButtonText}>草稿</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.approveButton} onPress={handleApprove} disabled={saving}>
          <Text style={styles.approveButtonText}>确认</Text>
        </TouchableOpacity>
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
  image: {
    width: '100%',
    height: 200,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  formSection: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 16,
  },
  confidenceBadge: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  fieldRow: {
    marginBottom: 16,
  },
  fieldLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  fieldInput: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  unitText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#999',
  },
  buttonRow: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    backgroundColor: '#fff',
  },
  rejectButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FF3B30',
  },
  rejectButtonText: {
    color: '#FF3B30',
    fontSize: 16,
    fontWeight: '500',
  },
  draftButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#666',
  },
  draftButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '500',
  },
  approveButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  approveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
