import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView, ActivityIndicator } from 'react-native';
import { useState, useEffect } from 'react';
import { useRouter } from 'expo-router';
import { getServerHost, setServerHost, testConnection } from '../config/serverConfig';

export default function SettingsPage() {
  const router = useRouter();
  const [host, setHost] = useState('');
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    loadCurrentHost();
  }, []);

  const loadCurrentHost = async () => {
    const currentHost = await getServerHost();
    setHost(currentHost);
  };

  const handleTest = async () => {
    if (!host.trim()) {
      Alert.alert('错误', '请输入服务器地址');
      return;
    }
    setTesting(true);
    setConnectionStatus(null);
    const result = await testConnection(host.trim());
    setConnectionStatus(result);
    setTesting(false);
  };

  const handleSave = async () => {
    if (!host.trim()) {
      Alert.alert('错误', '请输入服务器地址');
      return;
    }
    setSaving(true);
    try {
      await setServerHost(host.trim());
      Alert.alert('成功', '服务器地址已保存', [
        { text: '确定', onPress: () => router.back() }
      ]);
    } catch (error) {
      Alert.alert('错误', '保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>服务器地址</Text>
        <TextInput
          style={styles.input}
          value={host}
          onChangeText={setHost}
          placeholder="例如: 192.168.31.69 或 10.0.2.2"
          placeholderTextColor="#999"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />
        <Text style={styles.hint}>
          模拟器使用 10.0.2.2，真机使用局域网 IP（如 192.168.x.x）
        </Text>
        <Text style={styles.hint}>
          后端端口: 8000 | MinIO 端口: 9000
        </Text>
      </View>

      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.testButton, testing && styles.buttonDisabled]}
          onPress={handleTest}
          disabled={testing}
        >
          {testing ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.testButtonText}>测试连接</Text>
          )}
        </TouchableOpacity>

        {connectionStatus && (
          <View style={[
            styles.statusBox,
            connectionStatus.ok ? styles.statusSuccess : styles.statusError
          ]}>
            <Text style={[
              styles.statusText,
              connectionStatus.ok ? styles.statusTextSuccess : styles.statusTextError
            ]}>
              {connectionStatus.ok ? '✓ ' : '✗ '}{connectionStatus.message}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.saveButton, saving && styles.buttonDisabled]}
          onPress={handleSave}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.saveButtonText}>保存并返回</Text>
          )}
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
  section: {
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
  input: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333',
  },
  hint: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
    lineHeight: 18,
  },
  testButton: {
    backgroundColor: '#666',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  testButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  statusBox: {
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
  },
  statusSuccess: {
    backgroundColor: '#E8F5E9',
  },
  statusError: {
    backgroundColor: '#FFEBEE',
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  statusTextSuccess: {
    color: '#2E7D32',
  },
  statusTextError: {
    color: '#C62828',
  },
});
