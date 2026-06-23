# Thread System（FastAPI + Vite 重写版）

将原 `mobile_sys` 的 PHP 单体（页面控制器架构）重写为前后端分离：

- `backend/`：FastAPI 提供 JSON API（JWT 鉴权），通过 SQLAlchemy + PyMySQL 连接原有 MySQL，数据库表结构不变。
- `frontend/`：Vite + Vue 3 + TypeScript 单页应用（移动端优先），Pinia 管理登录态与报价临时列表。
- `mobile_sys/`：原 PHP 系统（保留备查，已停用）。

业务行为与原系统等价：登录、菜单、订单查询、订单详情、查价下单（折扣维护 / 临时列表 / 导出 Excel）。

## 一、后端（FastAPI）

### 1. 准备环境

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置

复制 `.env.example` 为 `.env` 并按需修改：

```bash
cp .env.example .env
```

关键项：

- `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS`：数据库连接（与原 `config.php` 一致）。
- `JWT_SECRET`：生产务必改为长随机串。
- `CORS_ORIGINS`：允许的前端来源（逗号分隔）。
- `LOCAL_USERS_JSON`：本地账号 `[[用户名, 密码, 真实姓名, 角色], ...]`，等价原 `local_users.php`。密码可填明文（兼容原行为），也可填 bcrypt 哈希。

### 3. 启动

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8900
```

接口文档：`http://127.0.0.1:8900/docs`

### 主要接口

- `POST /api/auth/login`：登录，返回 JWT。
- `GET /api/customers`、`GET /api/items`：全量主数据（前端本地联想用）。
- `GET /api/orders`：订单查询（参数 `cust_id/keyword/date_from/date_to`，最多 50 条）。
- `GET /api/orders/{order_id}`：订单头 + 明细。
- `GET /api/discounts`、`POST /api/discounts`：客户-产品折扣读取 / upsert。
- `POST /api/quote/prepare-line`：后端组装一条临时报价行。
- `POST /api/quote/export`：根据临时行导出 XLSX。

## 二、前端（Vite + Vue3）

### 1. 安装与开发

```bash
cd frontend
npm install
npm run dev
```

开发服务器默认 `http://localhost:5173`，已在 `vite.config.ts` 中把 `/api` 代理到 `http://127.0.0.1:8900`，因此本地联调无需额外处理跨域。

### 2. 生产构建

```bash
npm run build      # 产物在 frontend/dist
npm run preview    # 本地预览构建产物
```

## 三、本地联调顺序

1. 启动后端：`cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8900`
2. 启动前端：`cd frontend && npm run dev`
3. 浏览器打开 `http://localhost:5173`，用 `.env` 中配置的账号登录。

## 四、生产部署建议

- 后端：用 `uvicorn`（可加 `--workers`）或置于 `gunicorn -k uvicorn.workers.UvicornWorker` 之后，反向代理（Nginx）将 `/api` 转发到后端端口。
- 前端：`npm run build` 后将 `dist/` 交给 Nginx 作为静态站点；同域下 `/api` 反代到后端即可，`CORS_ORIGINS` 配置为实际域名。
- 安全：务必修改 `JWT_SECRET`，`.env` 不要提交到仓库（已在 `.gitignore` 中）。

## 五、与原系统的行为对照（关键点）

- 登录：账号/密码为空 -> “账号密码不能为空”；错误 -> “账号或密码错误”。
- 订单查询：聚合 `orders + customers + order_detail + chuhuo_wuliu`，最多 50 条，状态码 1-7 中文映射，状态 7 显示“全部出货结单”。
- 折扣保存：按 `cust_yongjin_p / cust_zhekou_jiajia` 推导并写入 `yongjin_fangshi`（只有加价→3、只有佣金比例→2、都有→5）。
- 导出 Excel：固定表头、供应商名写死“高士线业（深圳）有限公司”、佣金方式导出映射（只有加价→固定价格、只有佣金比例→固定比例、都有→固定比例+加价）、文件名 `quote_YYYYMMDD_HHMMSS.xlsx`。
  - 注意：导出映射与折扣保存的 2/3 含义在原系统中即相反，此处刻意保留原行为。
- 临时报价列表：原存于 PHP Session，现存于前端 Pinia + localStorage；数量为 0 不加入；支持删除单行 / 清空。
