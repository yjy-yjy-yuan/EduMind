# EduMind 数据库构建说明

后端使用 **MySQL**，表结构由 **SQLAlchemy** 根据模型自动创建（无 Alembic 迁移时可直接用应用或脚本建表）。按下面步骤即可完成「建库 + 建表」。

---

## 一、准备 MySQL

### 1. 安装 MySQL

- **macOS（Homebrew）**：`brew install mysql`，然后 `brew services start mysql`
- **Windows**：从 [MySQL 官网](https://dev.mysql.com/downloads/installer/) 下载安装
- **Docker**：`docker run -d --name mysql-edumind -e MYSQL_ROOT_PASSWORD=your_password -e MYSQL_DATABASE=edumind -p 3306:3306 mysql:8.0 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci`

### 2. 创建数据库（若未用 Docker 的 MYSQL_DATABASE）

登录 MySQL 后执行：

```sql
CREATE DATABASE edumind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

或命令行一行：

```bash
mysql -u root -p -e "CREATE DATABASE edumind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

---

## 二、配置连接

在 **backend_fastapi** 目录下：

1. 复制环境配置：`cp .env.example .env`
2. 编辑 `.env`，修改数据库连接（库名、用户名、密码、主机、端口）：

```bash
# 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/edumind
```

- 本机 MySQL：主机一般为 `localhost`，端口 `3306`
- 若用 Docker 且未在 run 时建库，需先执行上面的 `CREATE DATABASE edumind`，再在 `.env` 里填同一库名

---

## 三、建表（两种方式任选其一）

### 方式 1：启动应用时自动建表（推荐）

表结构在 **首次启动 FastAPI 应用** 时自动创建（`main.py` 的 lifespan 里会执行 `Base.metadata.create_all(bind=engine)`）。

```bash
cd backend_fastapi
conda activate edumind   # 或你的虚拟环境
python run.py
```

看到日志里出现「数据库表创建成功」「上传目录已就绪」即表示数据库和表都已就绪。

### 方式 2：用脚本单独建表

不启动完整应用，只建表：

```bash
cd backend_fastapi
conda activate edumind
python scripts/init_db.py
```

或只创建表不打印表结构信息：

```bash
python scripts/init_db.py --create
```

查看表结构说明：

```bash
python scripts/init_db.py --info
```

---

## 四、验证

1. **连接是否正常**：启动后端后无报错，且日志有「数据库表创建成功」。
2. **表是否生成**：在 MySQL 里执行 `USE edumind; SHOW TABLES;`，应能看到 `videos`、`users`、`subtitles`、`notes`、`note_timestamps`、`questions` 等表（具体以当前模型为准）。
3. **上传视频**：通过接口上传一个视频后，在 `videos` 表中应有一条新记录，且 `backend_fastapi/uploads/` 下有对应文件。

---

## 五、常见问题

| 问题 | 处理 |
|------|------|
| `Access denied for user` | 检查 `.env` 中 `DATABASE_URL` 的用户名、密码是否正确；MySQL 是否允许该用户从本机登录。 |
| `Unknown database 'edumind'` | 先执行 `CREATE DATABASE edumind ...` 创建数据库。 |
| `Can't connect to MySQL server` | 确认 MySQL 已启动；端口是否为 3306；若用 Docker 是否映射了 3306。 |
| 表已存在 / 想改表结构 | 当前项目通过 `create_all` 建表，只会创建不存在的表，不会改已有表。若要改结构，需手动改模型后删表重建，或后续引入 Alembic 做迁移。 |

---

## 六、小结

1. 安装并启动 MySQL，创建数据库 **edumind**（utf8mb4）。
2. 在 **backend_fastapi/.env** 中配置 **DATABASE_URL**。
3. 建表二选一：**启动应用**（`python run.py`）或运行 **`python scripts/init_db.py`**。

完成以上步骤后，数据库即构建完毕，可正常使用视频上传、列表、播放等功能。
