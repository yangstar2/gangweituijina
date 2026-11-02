# 腾讯云部署说明（SQLite · 无真实密钥）

目标：把 `qisi_ai_kejian/backend` 跑在腾讯云上，小程序指向你的 HTTPS 域名。数据库继续用 **SQLite3**（单机足够本阶段）。

## 推荐形态

| 方案 | 适用 |
|------|------|
| **轻量应用服务器 Lighthouse + Docker** | 最快上线，单机 SQLite |
| **CVM + Docker Compose** | 需自行装 Docker |
| **TKE / 云托管** | 后续；注意 SQLite 需挂持久卷，多副本慎用 |

本仓库提供：

- `backend/Dockerfile`
- `docker-compose.yml`（仓库 `qisi_ai_kejian/` 下）
- `backend/.env.example`（密钥占位）

## 1. 准备机器

1. 开通 Lighthouse / CVM（建议 Ubuntu 22.04+）
2. 安全组放行：`22`、`80`、`443`（以及调试用的 `8000` 可仅内网）
3. 安装 Docker（Lighthouse 应用镜像可自带）

```bash
# 示例
sudo apt update && sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
```

## 2. 拉取代码并启动

```bash
git clone <YOUR_REPO> && cd <REPO>/qisi_ai_kejian
cp backend/.env.example backend/.env
# 编辑 backend/.env — 填入微信 / 支付 / 管理员口令（勿提交）

docker compose up -d --build
curl http://127.0.0.1:8000/api/health
```

SQLite 文件在 Docker volume `qisi_sqlite` → 容器内 `/data/qisi.db`。备份：

```bash
docker compose exec api ls -la /data
# 或 docker run --rm -v qisi_ai_kejian_qisi_sqlite:/data -v $(pwd):/backup alpine \
#   cp /data/qisi.db /backup/qisi-$(date +%F).db
```

## 3. HTTPS 与域名

小程序要求 **合法 HTTPS 域名**（不再关闭校验）：

1. 域名解析到云主机公网 IP
2. 用 Nginx / Caddy 反代到 `127.0.0.1:8000`
3. 申请证书（腾讯云 SSL 免费证书或 Let's Encrypt）
4. 微信公众平台 → 开发 → 开发管理 → 服务器域名：request 合法域名填你的 API 域名
5. 修改小程序 `miniprogram/app.js` 的 `apiBase` 为 `https://api.your-domain.com`

Nginx 片段示例：

```nginx
server {
  listen 443 ssl;
  server_name api.your-domain.com;
  ssl_certificate     /etc/ssl/your.pem;
  ssl_certificate_key /etc/ssl/your.key;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## 4. 微信支付回调

1. 商户平台配置支付授权目录 / JSAPI
2. 将 `WECHAT_PAY_NOTIFY_URL` 设为 `https://api.your-domain.com/api/pay/notify/wechat`
3. 当前实现为 **mock 验签**；上线前在 `mock_wechat.verify_notify_signature` 换官方 APIv3 验签与回调解密
4. 本地联调可用 `POST /api/pay/notify/mock`

## 5. 管理后台

浏览器打开：`https://api.your-domain.com/admin/members`  
Basic Auth：`ADMIN_USERNAME` / `ADMIN_PASSWORD`（务必改掉默认值）。

## 6. 腾讯云其它服务（可选后续）

| 服务 | 用途 | 现状 |
|------|------|------|
| 混元大模型 | PPT/试卷生成 | `mock-hunyuan` 占位 |
| COS | 课件文件落盘 | 未接；artifact JSON 在 SQLite |
| 云数据库 | 多实例 | 暂用 SQLite；迁库时换连接串即可 |
| 密钥管理 KMS | 存支付证书 | 推荐，勿把密钥打进镜像 |

## 7. 健康检查与回滚

```bash
curl -fsS https://api.your-domain.com/api/health
docker compose logs -f api
docker compose down && docker compose up -d --build
```

**无真实密钥原则：** 镜像与仓库只保留占位符；生产用环境变量 / 密文注入。
