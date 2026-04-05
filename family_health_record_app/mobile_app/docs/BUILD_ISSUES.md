# Android APK 编译问题汇总

## 环境配置

- **操作系统**: Windows
- **项目路径**: `C:\Users\Administrator\qa-prompts\family_health_record_app\mobile_app`
- **Gradle 版本**: 8.14.3
- **Node.js**: 通过 nvm 管理
- **代理**: Clash (127.0.0.1:10800)

---

## 问题 1: 网络代理导致依赖下载失败

### 错误信息
```
Could not GET 'https://repo.maven.apache.org/maven2/...'
Connect to 127.0.0.1:7890 [/127.0.0.1] failed: Connection refused
```

### 原因
Gradle 未正确配置代理，且 `.gradle/gradle.properties` 中 HTTPS 端口被误设为 7890。

### 解决方案
1. 修改 `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx2048m -XX:MaxMetaspaceSize=512m \
  -Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=10800 \
  -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=10800

systemProp.http.proxyHost=127.0.0.1
systemProp.http.proxyPort=10800
systemProp.https.proxyHost=127.0.0.1
systemProp.https.proxyPort=10800
```

2. 修正 `~/.gradle/gradle.properties` 中的 HTTPS 端口为 10800

---

## 问题 2: Expo 依赖版本不匹配

### 错误信息
```
expo-constants:compileDebugKotlin FAILED
Unresolved reference 'service'
```

### 原因
`package.json` 中的 expo 相关依赖版本与 Expo SDK 54 不兼容。

### 解决方案
修正 `package.json` 中的依赖版本:

```json
{
  "dependencies": {
    "expo": "~54.0.33",
    "expo-constants": "~18.0.13",
    "expo-image-picker": "~17.0.10",
    "expo-linking": "~8.0.11",
    "expo-router": "~6.0.23",
    "react-native-screens": "~4.16.0",
    "react-native-safe-area-context": "~5.6.0"
  }
}
```

---

## 问题 3: Windows 路径长度超过 260 字符限制

### 错误信息
```
ninja: error: Stat(...RNCSafeAreaViewShadowNode.cpp.o):
Filename longer than 260 characters
```

### 原因
- 项目路径深度较大
- C++ 编译产物路径过长
- Windows 默认路径限制

### 解决方案
1. 启用 Windows 长路径支持:
```cmd
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
```

2. 禁用 New Architecture (可选，但能减少 C++ 编译):
```properties
newArchEnabled=false
```

3. 减少构建的 CPU 架构:
```properties
reactNativeArchitectures=arm64-v8a
```

---

## 最终配置

### gradle.properties
```properties
org.gradle.jvmargs=-Xmx2048m -XX:MaxMetaspaceSize=512m \
  -Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=10800 \
  -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=10800

systemProp.http.proxyHost=127.0.0.1
systemProp.http.proxyPort=10800
systemProp.https.proxyHost=127.0.0.1
systemProp.https.proxyPort=10800

android.useAndroidX=true
newArchEnabled=false
hermesEnabled=true
```

### 构建命令
```bash
cd android
export HTTP_PROXY=http://127.0.0.1:10800
export HTTPS_PROXY=http://127.0.0.1:10800
./gradlew assembleDebug --no-daemon
```

---

## 输出 APK

- **路径**: `mobile_app/android/app/build/outputs/apk/debug/app-debug.apk`
- **大小**: ~107 MB
- **架构**: arm64-v8a