import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import DateTimePicker from '@react-native-community/datetimepicker';
import { memberService } from '../../api/services';
import type { CreateMemberDTO } from '../../api/models';
import { GENDER_LABELS, MEMBER_TYPE_LABELS } from '../../constants/api';

export default function NewMemberPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [gender, setGender] = useState<'male' | 'female'>('male');
  const [dateOfBirth, setDateOfBirth] = useState(new Date());
  const [memberType, setMemberType] = useState<'child' | 'adult' | 'senior'>('child');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('错误', '请输入姓名');
      return;
    }

    setSaving(true);
    try {
      const data: CreateMemberDTO = {
        name: name.trim(),
        gender,
        date_of_birth: dateOfBirth.toISOString().split('T')[0],
        member_type: memberType,
      };
      await memberService.create(data);
      router.back();
    } catch (error) {
      Alert.alert('错误', '创建失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  const calculateMemberType = (dob: Date) => {
    const today = new Date();
    const age = today.getFullYear() - dob.getFullYear();
    if (age < 18) return 'child';
    if (age < 60) return 'adult';
    return 'senior';
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.form}>
        <Text style={styles.label}>姓名</Text>
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={setName}
          placeholder="请输入姓名"
          placeholderTextColor="#999"
        />

        <Text style={styles.label}>性别</Text>
        <View style={styles.genderRow}>
          <TouchableOpacity
            style={[styles.genderButton, gender === 'male' && styles.genderButtonActive]}
            onPress={() => setGender('male')}
          >
            <Text style={[styles.genderText, gender === 'male' && styles.genderTextActive]}>
              {GENDER_LABELS.male}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.genderButton, gender === 'female' && styles.genderButtonActive]}
            onPress={() => setGender('female')}
          >
            <Text style={[styles.genderText, gender === 'female' && styles.genderTextActive]}>
              {GENDER_LABELS.female}
            </Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.label}>出生日期</Text>
        <TouchableOpacity
          style={styles.dateInput}
          onPress={() => setShowDatePicker(true)}
        >
          <Text style={styles.dateText}>{formatDate(dateOfBirth)}</Text>
        </TouchableOpacity>
        {showDatePicker && (
          <DateTimePicker
            value={dateOfBirth}
            mode="date"
            display="default"
            onChange={(event, date) => {
              setShowDatePicker(false);
              if (date) {
                setDateOfBirth(date);
                setMemberType(calculateMemberType(date));
              }
            }}
          />
        )}

        <Text style={styles.label}>成员类型</Text>
        <View style={styles.typeRow}>
          {(['child', 'adult', 'senior'] as const).map((type) => (
            <TouchableOpacity
              key={type}
              style={[styles.typeButton, memberType === type && styles.typeButtonActive]}
              onPress={() => setMemberType(type)}
            >
              <Text style={[styles.typeText, memberType === type && styles.typeTextActive]}>
                {MEMBER_TYPE_LABELS[type]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={saving}
        >
          <Text style={styles.saveButtonText}>
            {saving ? '保存中...' : '保存并开始记录'}
          </Text>
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
  form: {
    padding: 16,
  },
  label: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  genderRow: {
    flexDirection: 'row',
    gap: 12,
  },
  genderButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e5e5',
  },
  genderButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  genderText: {
    fontSize: 16,
    color: '#333',
  },
  genderTextActive: {
    color: '#fff',
  },
  dateInput: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
  },
  dateText: {
    fontSize: 16,
    color: '#333',
  },
  typeRow: {
    flexDirection: 'row',
    gap: 12,
  },
  typeButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e5e5',
  },
  typeButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  typeText: {
    fontSize: 14,
    color: '#333',
  },
  typeTextActive: {
    color: '#fff',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 32,
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
