import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { useState, useEffect } from 'react';
import { useWindowDimensions } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { LineChart } from 'react-native-chart-kit';
import { trendService, reviewService } from '../../../api/services';
import { splitSeriesBySide } from '../../../utils';
import type { TrendSeries, ReviewTask, RevisedItem } from '../../../api/models';
import { METRIC_LABELS } from '../../../constants/api';

const METRICS = ['axial_length', 'height', 'weight', 'vision_acuity', 'glucose', 'tc', 'tg', 'hdl', 'ldl', 'hemoglobin', 'hba1c'];
const RANGES = ['1m', '3m', '6m', '1y'];

export default function TrendsPage() {
  const router = useRouter();
  const { id, metric = 'axial_length', range = '3m' } = useLocalSearchParams<{ id: string; metric?: string; range?: string }>();
  const [trends, setTrends] = useState<TrendSeries | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentMetric, setCurrentMetric] = useState(metric || 'axial_length');
  const [currentRange, setCurrentRange] = useState(range || '3m');

  useEffect(() => {
    loadTrends();
  }, [id, currentMetric, currentRange]);

  const loadTrends = async () => {
    setLoading(true);
    try {
      const data = await trendService.getTrends(id!, currentMetric, currentRange);
      setTrends(data);
    } catch (error) {
      console.error('Failed to load trends:', error);
    } finally {
      setLoading(false);
    }
  };

  const { width: windowWidth } = useWindowDimensions();
  const screenWidth = windowWidth - 32;

  const formatChartData = () => {
    if (!trends?.series?.length) return { labels: [], datasets: [{ data: [0] }] };
    
    const { leftData, rightData, labels } = splitSeriesBySide(trends.series);
    
    const displayLabels = labels.map(s => s.slice(5));
    const leftValues = leftData.map(s => Number(s.value));
    const rightValues = rightData.map(s => Number(s.value));
    
    if (rightValues.length > 0) {
      return {
        labels: displayLabels,
        datasets: [
          { data: leftValues, strokeWidth: 2 },
          { data: rightValues, strokeWidth: 2 },
        ],
      };
    }
    
    return {
      labels: displayLabels,
      datasets: [{ data: leftValues }],
    };
  };

  const chartData = formatChartData();

  return (
    <ScrollView style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.metricTabs}>
        {METRICS.map((m) => (
          <TouchableOpacity
            key={m}
            style={[styles.metricTab, currentMetric === m && styles.metricTabActive]}
            onPress={() => {
              setCurrentMetric(m);
              router.replace(`/member/${id}/trends?metric=${m}&range=${currentRange}`);
            }}
          >
            <Text style={[styles.metricTabText, currentMetric === m && styles.metricTabTextActive]}>
              {METRIC_LABELS[m] || m}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.rangeTabs}>
        {RANGES.map((r) => (
          <TouchableOpacity
            key={r}
            style={[styles.rangeTab, currentRange === r && styles.rangeTabActive]}
            onPress={() => {
              setCurrentRange(r);
              router.replace(`/member/${id}/trends?metric=${currentMetric}&range=${r}`);
            }}
          >
            <Text style={[styles.rangeTabText, currentRange === r && styles.rangeTabTextActive]}>
              {r === '1m' ? '1月' : r === '3m' ? '3月' : r === '6m' ? '6月' : '1年'}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {loading ? (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>加载中...</Text>
        </View>
      ) : trends?.series?.length ? (
        <>
          <View style={styles.chartContainer}>
            <LineChart
              data={chartData}
              width={screenWidth}
              height={220}
              chartConfig={{
                backgroundColor: '#fff',
                backgroundGradientFrom: '#fff',
                backgroundGradientTo: '#fff',
                decimalPlaces: 1,
                color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
                labelColor: () => '#666',
                propsForDots: { r: '4' },
              }}
              bezier
              style={styles.chart}
            />
          </View>

          {trends.reference_range && (
            <View style={styles.infoCard}>
              <Text style={styles.infoLabel}>参考区间</Text>
              <Text style={styles.infoValue}>{trends.reference_range}</Text>
            </View>
          )}

          {trends.comparison && 'left' in trends.comparison && (
            <View style={styles.comparisonCard}>
              <Text style={styles.comparisonTitle}>最近对比</Text>
              <View style={styles.comparisonRow}>
                <View style={styles.comparisonItem}>
                  <Text style={styles.comparisonLabel}>左眼</Text>
                  <Text style={styles.comparisonValue}>
                    {trends.comparison.left.current} ({trends.comparison.left.delta > 0 ? '+' : ''}{trends.comparison.left.delta})
                  </Text>
                </View>
                <View style={styles.comparisonItem}>
                  <Text style={styles.comparisonLabel}>右眼</Text>
                  <Text style={styles.comparisonValue}>
                    {trends.comparison.right.current} ({trends.comparison.right.delta > 0 ? '+' : ''}{trends.comparison.right.delta})
                  </Text>
                </View>
              </View>
            </View>
          )}

          {trends.comparison && 'current' in trends.comparison && (
            <View style={styles.comparisonCard}>
              <Text style={styles.comparisonTitle}>最近对比</Text>
              <Text style={styles.comparisonValue}>
                {trends.comparison.current} ({trends.comparison.delta > 0 ? '+' : ''}{trends.comparison.delta})
              </Text>
            </View>
          )}

          <View style={styles.historySection}>
            <Text style={styles.historyTitle}>历史记录</Text>
            {trends.series.map((point, index) => (
              <View key={index} style={styles.historyItem}>
                <Text style={styles.historyDate}>{point.date}</Text>
                <Text style={styles.historyValue}>
                  {point.side === 'left' ? '左: ' : point.side === 'right' ? '右: ' : ''}
                  {point.value}
                </Text>
              </View>
            ))}
          </View>
        </>
      ) : (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>暂无趋势数据</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    padding: 32,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  metricTabs: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
  },
  metricTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
  },
  metricTabActive: {
    backgroundColor: '#007AFF',
  },
  metricTabText: {
    fontSize: 14,
    color: '#666',
  },
  metricTabTextActive: {
    color: '#fff',
  },
  rangeTabs: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  rangeTab: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    marginRight: 8,
    borderRadius: 16,
    backgroundColor: '#f0f0f0',
  },
  rangeTabActive: {
    backgroundColor: '#34C759',
  },
  rangeTabText: {
    fontSize: 12,
    color: '#666',
  },
  rangeTabTextActive: {
    color: '#fff',
  },
  chartContainer: {
    backgroundColor: '#fff',
    margin: 16,
    borderRadius: 12,
    padding: 16,
  },
  chart: {
    borderRadius: 12,
  },
  infoCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 12,
    padding: 16,
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
  },
  infoValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginTop: 4,
  },
  comparisonCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 12,
    padding: 16,
  },
  comparisonTitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  comparisonRow: {
    flexDirection: 'row',
  },
  comparisonItem: {
    flex: 1,
  },
  comparisonLabel: {
    fontSize: 12,
    color: '#999',
  },
  comparisonValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  historySection: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    padding: 16,
  },
  historyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  historyItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  historyDate: {
    fontSize: 14,
    color: '#666',
  },
  historyValue: {
    fontSize: 14,
    color: '#333',
  },
  emptyContainer: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
});
