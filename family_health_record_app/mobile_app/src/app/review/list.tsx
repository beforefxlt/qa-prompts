import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'expo-router';
import { reviewService } from '../../api/services';
import type { ReviewTask } from '../../api/models';

export default function ReviewListPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadTasks = useCallback(async () => {
    try {
      const data = await reviewService.list();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load review tasks:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadTasks();
    setRefreshing(false);
  }, [loadTasks]);

  const renderTask = ({ item }: { item: ReviewTask }) => (
    <TouchableOpacity
      style={styles.taskCard}
      onPress={() => router.push(`/review/${item.id}`)}
    >
      <View style={styles.taskInfo}>
        <Text style={styles.taskDate}>
          {item.ocr_result?.exam_date || '未知日期'}
        </Text>
        <Text style={styles.taskId}>ID: {item.document_id.slice(0, 8)}</Text>
      </View>
      <View style={styles.confidenceBadge}>
        <Text style={styles.confidenceText}>
          {item.ocr_result?.confidence_score?.toFixed(2) || 'N/A'}
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>加载中...</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {tasks.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>暂无待审核任务</Text>
        </View>
      ) : (
        <FlatList
          data={tasks}
          keyExtractor={(item) => item.id}
          renderItem={renderTask}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
  listContent: {
    padding: 16,
  },
  taskCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  taskInfo: {
    flex: 1,
  },
  taskDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  taskId: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  confidenceBadge: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  confidenceText: {
    fontSize: 14,
    color: '#2E7D32',
    fontWeight: '500',
  },
});
