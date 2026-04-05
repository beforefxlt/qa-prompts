import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'expo-router';
import { memberService } from '../api/services';
import type { MemberProfile } from '../api/models';
import { MEMBER_TYPE_LABELS } from '../constants/api';

export default function HomeScreen() {
  const router = useRouter();
  const [members, setMembers] = useState<MemberProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadMembers = useCallback(async () => {
    try {
      const data = await memberService.list();
      setMembers(data);
    } catch (error) {
      console.error('Failed to load members:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadMembers();
    setRefreshing(false);
  }, [loadMembers]);

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyTitle}>欢迎使用家庭检查单管理</Text>
      <Text style={styles.emptySubtitle}>
        记录家人健康足迹，从添加第一位成员开始。我们将为您智能分析等核心指标趋势。
      </Text>
      <TouchableOpacity 
        style={styles.emptyButton}
        onPress={() => router.push('/member/new')}
      >
        <Text style={styles.emptyButtonText}>添加第一位成员</Text>
      </TouchableOpacity>
    </View>
  );

  const renderMemberCard = ({ item }: { item: MemberProfile }) => (
    <TouchableOpacity
      style={styles.memberCard}
      onPress={() => router.push(`/member/${item.id}`)}
    >
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{item.name.charAt(0)}</Text>
      </View>
      <View style={styles.memberInfo}>
        <Text style={styles.memberName}>{item.name}</Text>
        <Text style={styles.memberType}>{MEMBER_TYPE_LABELS[item.member_type]}</Text>
        <Text style={styles.lastCheck}>
          {item.last_check_date ? `最近: ${item.last_check_date}` : '尚无记录'}
        </Text>
      </View>
      {item.pending_review_count > 0 && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{item.pending_review_count}</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>加载中...</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <Stack.Screen 
        options={{ 
          title: '家庭成员',
          headerRight: () => (
            <TouchableOpacity onPress={() => router.push('/settings')}>
              <Text style={styles.settingsButton}>设置</Text>
            </TouchableOpacity>
          ),
        }} 
      />

      {members.length === 0 ? (
        renderEmptyState()
      ) : (
        <>
          <FlatList
            data={members}
            keyExtractor={(item) => item.id}
            renderItem={renderMemberCard}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
            ListFooterComponent={
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => router.push('/member/new')}
              >
                <Text style={styles.addButtonText}>+ 添加成员</Text>
              </TouchableOpacity>
            }
          />
          <View style={styles.tabBar}>
            <TouchableOpacity style={styles.tabItem}>
              <Text style={styles.tabText}>成员</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.tabItem}
              onPress={() => router.push('/review')}
            >
              <Text style={styles.tabText}>审核箱</Text>
            </TouchableOpacity>
          </View>
        </>
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
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  emptyButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  emptyButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
    paddingBottom: 80,
  },
  memberCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  avatarText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  memberInfo: {
    flex: 1,
  },
  memberName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  memberType: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  lastCheck: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  badge: {
    backgroundColor: '#FF3B30',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  addButton: {
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  addButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  tabBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e5e5e5',
    flexDirection: 'row',
    paddingVertical: 12,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
  },
  tabText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  settingsButton: {
    fontSize: 16,
    color: '#007AFF',
  },
});
