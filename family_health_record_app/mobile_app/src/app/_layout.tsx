import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: '家庭成员' }} />
      <Stack.Screen name="settings" options={{ title: '服务器设置' }} />
      <Stack.Screen name="review/index" options={{ title: '审核箱' }} />
      <Stack.Screen name="member/new" options={{ title: '新建成员' }} />
      <Stack.Screen name="member/[id]/index" options={{ title: '成员详情' }} />
      <Stack.Screen name="member/[id]/edit" options={{ title: '编辑成员' }} />
      <Stack.Screen name="member/[id]/trends" options={{ title: '趋势分析' }} />
      <Stack.Screen name="member/[id]/record/[recordId]" options={{ title: '检查详情' }} />
      <Stack.Screen name="member/[id]/manual-entry" options={{ title: '手工录入指标' }} />
    </Stack>
  );
}
