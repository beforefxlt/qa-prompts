# 移动端技术选型决策

> **版本**: v1.0.0  
> **最后更新**: 2026-04-04

## 1. 决策结论

| 项目 | 选择 | 备注 |
|------|------|------|
| **框架** | React Native + Expo SDK 52 | 官方推荐 |
| **语言** | TypeScript | 与 Web 端一致 |
| **路由** | expo-router | 文件路由，类似 Next.js App Router |
| **状态管理** | React Context + useReducer | 轻量，满足 MVP |
| **HTTP** | fetch (原生) | Expo 内置，无需额外依赖 |
| **图表** | react-native-chart-kit | RN 生态成熟 |
| **图片选择** | expo-image-picker | 相册/拍照统一入口 |
| **表单处理** | react-hook-form | 表单验证 |
| **日期选择** | @react-native-community/datetimepicker | 原生体验 |

## 2. 备选方案对比

### 2.1 跨平台框架对比

| 维度 | Flutter | React Native (Expo) | Kotlin Jetpack Compose |
|------|---------|---------------------|------------------------|
| **语言** | Dart | TypeScript | Kotlin |
| **渲染** | Skia 自绘 | 原生组件 | 原生组件 |
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **包体积** | ~25MB | ~15MB | ~10MB |
| **学习成本** | 需学 Dart | 熟悉 React 即可 | 需学 Kotlin |
| **Web 支持** | 需额外配置 | Expo Web | 不支持 |
| **热更新** | 支持 | 支持 | 不支持 |
| **AI Coding** | 成熟 | 成熟 | 一般 |

### 2.2 本项目选择理由

| 因素 | 选择 Expo 的理由 |
|------|------------------|
| **团队技能** | 团队更熟悉 TypeScript/JavaScript |
| **开发速度** | 无需 Native 环境配置，扫码即运行 |
| **Web 端复用** | 可共用 API 调用逻辑和业务模型 |
| **热更新** | 支持 OTA 更新，无需重新发布应用商店 |
| **生态丰富** | 1900+ 官方维护的 npm 包 |
| **维护成本** | 单一技术栈，统一维护 |

### 2.3 未选择 Flutter 的原因

- 需额外安装 Flutter SDK（Dart 语言）
- 与现有 Web 技术栈不统一
- AI Coding 生成 Dart 代码质量不如 TypeScript
- 初始包体积较大

### 2.4 未选择原生 Kotlin 的原因

- 需要 Native 开发环境配置
- 开发周期较长
- 不符合"AI Coding 友好"原则

## 3. 关键技术决策

### 3.1 路由方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| **expo-router** (选择) | 文件路由、自动代码分割、深度链接支持 | 需要理解文件系统路由约定 |
| React Navigation | 灵活、可控 | 需要手动配置路由表 |
| wix/react-native-navigation | 原生导航性能好 | 配置复杂 |

**理由**：expo-router 与 Next.js App Router 设计理念一致，便于 Web 端开发者快速上手。

### 3.2 状态管理

| 方案 | 优点 | 缺点 |
|------|------|------|
| **React Context + useReducer** (选择) | 无需额外依赖、轻量 | 大型场景需拆分 Provider |
| Redux Toolkit | 功能强大、调试方便 | 体积较大 |
| Zustand | 简洁、灵活 | 社区较小 |
| Jotai | 原子化、类型安全 | 学习曲线 |

**理由**：MVP 阶段业务简单，不需要复杂的状态管理。Context + useReducer 足够，且无额外依赖。

### 3.3 表单处理

| 方案 | 优点 | 缺点 |
|------|------|------|
| **react-hook-form** (选择) | 性能好、验证强大 | 需要学习 hook API |
| Formik | 文档丰富 | 性能略差 |
| Native base | 组件完整 | 绑定较深 |

**理由**：react-hook-form 是 React 表单处理的事实标准，性能优异。

### 3.4 图表方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| **react-native-chart-kit** (选择) | 基于 react-native-svg，配置灵活 | 大数据量性能一般 |
| react-native-svg-charts | SVG 渲染，图表丰富 | 维护不活跃 |
| Victory Native | 功能强大 | 体积较大 |

**理由**：chart-kit 足够满足趋势图需求，且基于 SVG 渲染，图表质量好。

## 4. 依赖清单

### 4.1 核心依赖

```json
{
  "dependencies": {
    "expo": "~52.0.0",
    "expo-router": "~4.0.0",
    "react": "18.3.1",
    "react-native": "0.76.6",
    "expo-image-picker": "~16.0.0",
    "react-native-chart-kit": "^6.12.0",
    "react-native-svg": "15.8.0",
    "react-hook-form": "^7.54.0",
    "@react-native-community/datetimepicker": "^8.0.0",
    "@expo/vector-icons": "^14.0.0"
  }
}
```

### 4.2 开发依赖

```json
{
  "devDependencies": {
    "@types/react": "~18.3.0",
    "typescript": "^5.3.0"
  }
}
```

## 5. 环境要求

| 项目 | 要求 |
|------|------|
| **Node.js** | >= 18.0.0 |
| **npm** | >= 9.0.0 |
| **Android Studio** | 2022+ (含 Android SDK) |
| **JDK** | 17 (LTS) |

## 6. 构建与发布

### 6.1 开发模式

```bash
# 安装依赖
npm install

# 启动开发服务器
npx expo start

# Android 真机/模拟器
npx expo run:android
```

### 6.2 构建 APK

```bash
# 生成 Android 原生项目
npx expo prebuild --platform android

# 构建 Debug APK
cd android && ./gradlew assembleDebug

# 构建 Release APK
cd android && ./gradlew assembleRelease
```

### 6.3 发布

| 渠道 | 方式 |
|------|------|
| **内测** | Expo EAS Build 或直接导出 APK |
| **应用商店** | Google Play 提审 |
| **内网分发** | 直接分发 APK 文件 |

## 7. 参考资源

- [Expo 官方文档](https://docs.expo.dev/)
- [expo-router 文档](https://docs.expo.dev/router/introduction/)
- [react-native-chart-kit 示例](https://github.com/indiesc/react-native-chart-kit)
- [React Hook Form 文档](https://react-hook-form.com/)

## 8. 决策历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-04 | v1.0.0 | 初始决策：Expo + TypeScript |
