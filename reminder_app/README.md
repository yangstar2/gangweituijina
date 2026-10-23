# AI 个人提醒助手（Stage 01）

Flutter + Dart，Android 优先；保留 iOS 工程目录以便后续扩展。

**本阶段范围：** UI + 导航 + 假数据 / 内存仓库。  
**不含：** 真实 AI API、系统本地通知调度、SQLite。

## 功能页

1. **首页 / 创建** — 问候、自然语言输入、「10 分钟后」「指定时间」、今日待办 / 即将提醒 / 已完成（mock）
2. **解析确认** — 展示完整日期、时间、重复；修改 / 确认保存（仅写入内存）
3. **提醒列表** — 编辑 / 删除 / 完成；筛选 待办 / 已完成
4. **提醒设置** — 日期、时间、重复：不重复 / 每天 / 每周 / 自定义星期

## 环境要求

- Flutter 3.47+（Stable）
- Android SDK（建议 API 35/36）+ 接受过 SDK licenses
- JDK 17+（本机已测 OpenJDK 21）

## 运行（Android 模拟器 / 真机）

```bash
cd reminder_app

# 依赖
flutter pub get

# 查看设备
flutter devices

# 启动（需已开 emulator 或连接真机）
flutter run

# 或安装 debug APK
flutter build apk --debug
adb install build/app/outputs/flutter-apk/app-debug.apk
```

静态检查与测试：

```bash
flutter analyze
flutter test
```

## 工程结构（为后续阶段预留）

```
lib/
  domain/          # 模型 + 仓库/服务接口
  data/            # 内存仓库、Mock AI、通知 stub
  presentation/    # 四页 UI
  theme/           # 学生友好配色与字体
```

- `AiParser` / `NotificationScheduler`：接口已留，Stage 01 为 stub
- `ReminderRepository`：Stage 01 为 `InMemoryReminderRepository`；后续换 SQLite

## Stage 02 预告（通知）

- 接入 `flutter_local_notifications` + 精确闹钟权限
- 开机后根据持久化数据重挂提醒
- 落库成功后再 `schedule`；删除/改期同步 cancel/reschedule
