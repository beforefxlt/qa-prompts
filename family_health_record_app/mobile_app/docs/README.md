# 家庭检查单管理应用 - 移动端

> **版本**: v1.0.0  
> **技术栈**: React Native + Expo SDK 52 + TypeScript

## 1. 项目概述

本项目是家庭检查单管理应用的移动端（Android）实现，基于 [Web 版](https://github.com/your-repo/family_health_record_app) 迁移，使用 Expo 框架开发。

## 2. 功能特性

| 功能 | 状态 | 说明 |
|------|------|------|
| 成员管理 | ✅ | 创建、编辑、删除成员档案 |
| 检查单上传 | ✅ | 拍照/相册选择，OCR 识别 |
| OCR 审核 | ✅ | 字段编辑、置信度显示、冲突提示 |
| 趋势图表 | ✅ | 指标趋势、参考区间、报警提示 |
| 检查详情 | ✅ | 单次检查记录展示 |

## 3. 技术架构

| 层级 | 技术选型 |
|------|----------|
| 框架 | Expo SDK 52 |
| 语言 | TypeScript |
| 路由 | expo-router (文件路由) |
| 状态管理 | React Context + useReducer |
| HTTP | fetch (原生) |
| 图表 | react-native-chart-kit |
| 图片选择 | expo-image-picker |
| 表单 | react-hook-form |
| 日期选择 | @react-native-community/datetimepicker |

## 4. 目录结构

```
mobile_app/
├── src/
│   ├── api/                    # API 客户端层
│   │   ├── client.ts           # fetch 封装
│   │   ├── models/             # TypeScript 类型定义
│   │   └── services/           # 各资源服务函数
│   ├── app/                    # 页面（expo-router）
│   │   ├── _layout.tsx         # 根布局 + 底部 Tab
│   │   ├── index.tsx           # 首页（成员列表）
│   │   ├── member/
│   │   │   ├── new.tsx         # 创建成员
│   │   │   └── [id]/
│   │   │       ├── index.tsx  # 成员 Dashboard
│   │   │       ├── edit.tsx   # 编辑成员
│   │   │       ├── trends.tsx # 趋势页
│   │   │       └── record/
│   │   │           └── [recordId].tsx # 检查详情
│   │   └── review/
│   │       └── [taskId].tsx   # OCR 审核页
│   ├── components/            # 通用组件
│   ├── hooks/                  # 自定义 Hooks
│   ├── utils/                  # 工具函数
│   └── constants/              # 常量配置
├── docs/                       # 项目文档
├── android/                    # Android 原生项目（生成）
├── app.json                    # Expo 配置
└── package.json
```

## 5. 快速开始

### 5.1 环境要求

| 项目 | 要求 |
|------|------|
| Node.js | >= 18.0.0 |
| npm | >= 9.0.0 |
| Android Studio | 2022+ (含 Android SDK) |
| JDK | 17 (LTS) |

### 5.2 安装

```bash
# 进入项目目录
cd family_health_record_app/mobile_app

# 安装依赖
npm install
```

### 5.3 运行

```bash
# 启动开发服务器
npm start

# 运行 Android（需 Android Studio / 模拟器）
npm run android

# 运行 Web（预览）
npm run web
```

### 5.4 APK 构建

#### Debug APK（开发调试，需 Metro 服务器）

```bash
# 生成 Android 原生项目
npx expo prebuild --platform android

# 构建 Debug APK
cd android && ./gradlew assembleDebug

# APK 输出位置
# android/app/build/outputs/apk/debug/app-debug.apk
```

> ⚠️ **Debug APK 依赖 Metro dev server**（默认 `ws://10.0.2.2:8081`），必须同时运行 `npm start` 才能加载 JS 代码。模拟器上无法独立运行。

#### Release APK（推荐，独立运行）

```bash
# 生成 Android 原生项目（如未生成）
npx expo prebuild --platform android

# 构建 Release APK
cd android
./gradlew assembleRelease

# APK 输出位置
# android/app/build/outputs/apk/release/app-release.apk
```

> ✅ **Release APK 已将 JS bundle 内嵌到 APK 中**，无需 Metro 服务器即可独立运行。

### 5.5 安装到模拟器

```bash
# 查看已连接设备
adb devices

# 安装 APK
adb install -r android/app/build/outputs/apk/release/app-release.apk

# 清理旧数据后重新安装（推荐）
adb shell pm clear com.familyhealth.healthrecord
adb install -r android/app/build/outputs/apk/release/app-release.apk
```

## 6. API 配置

### 6.1 运行时服务器配置（推荐）

移动端支持在应用内 **动态配置服务器地址**，无需重新编译：

- 进入 **首页 → 设置** 按钮，打开服务器设置页
- 输入服务器主机地址（不含协议和端口）
- 点击 **测试连接** 验证连通性
- 点击 **保存并返回** 生效

| 场景 | 推荐配置 |
|------|----------|
| Android 模拟器 | `10.0.2.2` |
| 真机（同一局域网） | `192.168.x.x`（电脑 IP） |
| 默认值 | `10.0.2.2`（模拟器地址） |

配置存储在 `AsyncStorage` 中，修改后立即生效。后端端口固定为 `8000`，MinIO 端口固定为 `9000`。

### 6.2 后端服务要求

- 运行在 `http://localhost:8000`
- 开放 CORS 跨域访问
- 无需认证 Token（内网免登录）
- `AndroidManifest.xml` 已配置 `usesCleartextTraffic="true"` 支持 HTTP 明文请求

## 7. 参考文档

- [移动端 UI 规格](../../docs/specs/MOBILE_UI_SPEC.md)
- [移动端 API 对接说明](../../docs/specs/MOBILE_API_CONTRACT.md)
- [技术选型决策](../../docs/specs/MOBILE_TECH_DECISION.md)
- [后端 API 契约](../../docs/specs/API_CONTRACT.md)
- [构建问题汇总](./BUILD_ISSUES.md) - **编译/部署问题必查**

## 8. 开发规范

### 8.1 代码风格

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 样式使用 StyleSheet 或 Tailwind（如已配置）
- 命名使用 camelCase

### 8.2 API 调用

- 所有 API 调用封装在 `src/api/services/` 目录
- 使用 React Query 或 useEffect + useState 管理数据获取状态
- 错误处理统一在 client 层捕获

### 8.3 测试

```bash
# 运行测试
npm test

# 类型检查
npx tsc --noEmit
```

## 9. 常见问题

### Q: 模拟器无法访问后端？

A: Android 模拟器访问主机 localhost 使用 `10.0.2.2`，而非 `localhost`。

### Q: 图片上传失败？

A: 检查后端 CORS 配置，确保允许来自移动端的请求。

### Q: 构建 APK 失败？

A: 确保 Android SDK 和 JDK 17 已正确配置。运行 `echo $ANDROID_HOME` 确认。

## 10. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-04-04 | 初始版本，实现核心功能 |
