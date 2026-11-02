# qisi_ai_kejian

微信小程序 + Python（FastAPI）+ SQLite3。本目录为独立产品代码，与仓库根目录历史无关。

**已覆盖：** 追问老师澄清 → 大纲 → 风格/模型 → 6 页预览 → **正式生成完整 PPT / 试卷（mock，落库 artifacts）**。会员支付 / 管理后台 / 腾讯云部署见后续 PR。

## 目录

| 路径 | 作用 |
|------|------|
| `backend/` | FastAPI + SQLite |
| `miniprogram/` | 微信小程序原生前端 |
| `backend/app/services/mock_ai.py` | 追问老师 + 预览 + **PPT/试卷生成** mock |
| `backend/app/routers/generate.py` | 正式生成 API |
| `backend/app/routers/sessions.py` | 会话 / 聊天 / 大纲 / 预览 |
| `backend/app/routers/catalog.py` | 风格 / 模型列表 |
| `miniprogram/pages/chat/` | 追问老师对话 |
| `miniprogram/pages/outline/` | 大纲确认 |
| `miniprogram/pages/style-filter/` | 风格筛选 |
| `miniprogram/pages/model-select/` | PPT 模型选择 |
| `miniprogram/pages/preview/` | 约 6 页预览 + 正式生成入口 |
| `miniprogram/pages/result-ppt/` | 完整课件结果 |
| `miniprogram/pages/result-exam/` | 完整试卷结果 |

## 启动后端

```bash
cd qisi_ai_kejian/backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或：`bash run.sh`

健康检查：`GET http://127.0.0.1:8000/api/health`

API 文档：`http://127.0.0.1:8000/docs`

## 启动小程序

1. 安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 导入项目目录：`qisi_ai_kejian/miniprogram`
3. AppID 可用测试号；`project.config.json` 中为 mock id
4. 详情 → 本地设置 → **不校验合法域名**（对接本机 `http://127.0.0.1:8000`）
5. 如真机调试，把 `miniprogram/app.js` 里 `apiBase` 改成电脑局域网 IP

## 本地联调流程（mock）

1. 首页选「做课件」或「出试卷」
2. 与追问老师对话 **至少 3 轮**（mock 规则在第 3 轮产出大纲）
3. 确认大纲 → 选风格 → 选模型 → 滑动查看约 6 页预览
4. 点「正式生成」→ 查看完整 PPT 或试卷（写入 `artifacts` 表）

## 后续扩展预留

- `members` / `pay_orders` 表已 stub（会员与支付下一切片）
- `mock_wechat.create_prepay` 可换真实微信支付
- `mock_ai.generate_ppt` / `generate_exam` 可换成真实 Provider
