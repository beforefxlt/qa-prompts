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

## 问题 4: Debug APK 在模拟器上无法连接服务器

### 现象
- Debug APK 安装后白屏或加载失败
- 日志显示 `Couldn't connect to "ws://10.0.2.2:8081"` 和 `Network request failed`

### 原因
Debug APK 不包含内嵌的 JS bundle，运行时依赖 Metro dev server（`ws://10.0.2.2:8081`）动态加载 JS 代码。如果 Metro 未启动，JS 无法加载，应用表现为白屏或功能异常。

### 解决方案
**使用 Release APK 部署到模拟器/真机**：

```bash
cd android
./gradlew assembleRelease
```

Release APK 在构建时已将 JS bundle 打包进 APK（`createBundleReleaseJsAndAssets` 任务），无需 Metro 即可独立运行。

### 服务器地址配置
Release APK 使用 `src/config/serverConfig.ts` 管理服务器地址：
- **默认值**: `10.0.2.2`（Android 模拟器访问主机）
- **运行时修改**: 应用内 → 首页 → 设置 → 输入服务器地址 → 测试连接 → 保存
- **存储方式**: AsyncStorage（`@server_host` key），修改后立即生效
- **不依赖** `.env` 或编译时环境变量

> ⚠️ 如果之前安装过旧版本，建议先 `adb shell pm clear com.familyhealth.healthrecord` 清理 AsyncStorage 缓存数据后再安装新版本。

---

## 输出 APK

| 类型 | 路径 | 大小 | 说明 |
|------|------|------|------|
| Debug | `android/app/build/outputs/apk/debug/app-debug.apk` | ~107 MB | 需 Metro 服务器，仅开发调试 |
| Release | `android/app/build/outputs/apk/release/app-release.apk` | ~57 MB | 内嵌 JS bundle，可独立运行 |