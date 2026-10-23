# AI 个人提醒助手（uni-app）

面向初中生的 Android 优先个人提醒助手。**阶段 01**：UI + 导航 + 内存/模拟数据。  
**不包含**：真实本地推送调度、真实 AI API、云同步。

> 本目录为当前**主工程**。仓库内若仍有 `reminder_app/`（Flutter 阶段 01），仅作参考，不再作为交付主栈。

## 技术栈

- uni-app（Vue 3 + Vite + TypeScript）
- 目标：App-Plus（Android 优先；工程可延伸 iOS）
- 状态：内存 reactive store；通知 / AI / SQLite 仅 stub

## 页面

| 路径 | 说明 |
|------|------|
| `pages/home/index` | 问候 + 自然语言输入 + 快捷「10 分钟后」「指定时间」+ 今日/即将/已完成 |
| `pages/confirm/index` | AI 解析确认（完整年月日、时间、重复）→ 修改 / 确认保存 |
| `pages/list/index` | 提醒列表：编辑 / 删除 / 完成；筛选待办 / 已完成 |
| `pages/settings/index` | 日期、时间、重复（不重复 / 每天 / 每周 / 自定义星期） |

## 环境要求

- Node.js **18+**（推荐 20）
- 包管理：`npm` 或 `pnpm`
- **真机 / 模拟器 App 打包**：建议 [HBuilderX](https://www.dcloud.io/hbuilderx.html) 3.6.7+（Vue3/Vite）
- CLI 可编译 H5 / 小程序资源；**云端打 APK/IPA 通常仍需 HBuilderX**

## 安装

```bash
cd reminder_uniapp
npm install
# 或：pnpm install
```

## 运行（CLI）

```bash
# H5 浏览器预览（阶段 01 验收最方便）
npm run dev:h5

# 类型检查
npm run type-check

# 生产构建 H5
npm run build:h5

# App 资源（需本机/HBuilderX 再打包安装）
npm run dev:app
npm run build:app
```

浏览器打开终端提示的本地地址（一般为 `http://localhost:5173`）。

## 运行（HBuilderX）

1. 用 HBuilderX 打开本目录 `reminder_uniapp/`（或仓库根目录后选中本项目）。
2. 运行 → 运行到浏览器 / 运行到手机或模拟器 → Android。
3. 若 Node 版本提示异常：HBuilderX → 设置 → 运行配置 → 指定本机 Node 路径后重启。

### Android 真机注意

- 阶段 01 **不会**申请通知/精确闹钟权限（尚未调度系统通知）。
- USB 调试或 Wi‑Fi 真机运行均可；首次需同意安装未知来源（视 ROM 而定）。
- 正式 APK：发行 → 原生 App-Cloud 打包（需 DCloud 账号与证书配置）。

## 目录要点

```
src/
  domain/          # Reminder 领域模型
  store/           # 内存数据 + draft 传递
  services/        # mock AI / 通知 stub / SQLite stub
  pages/           # 四页 UI
  components/      # ReminderTile 等
```

## 后续阶段（预留）

- 阶段 02：SQLite 持久化 + App 本地通知（杀进程 / 重启重挂）
- 阶段 03：真实 AI → JSON 解析；调度与落库仍由 App 拥有
