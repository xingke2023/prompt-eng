# Seedance 视频提示词工程工具 — CLAUDE.md

## 项目概述

一个 Flask Web 应用，帮助用户为 **Seedance**（字节跳动视频生成模型）生成高质量的英文提示词。核心功能：结构化单镜头提示词生成、多镜头分镜脚本生成、提示词优化、可复用素材库。

- **运行地址**：`http://172.31.27.190:8129`
- **启动命令**：`python3 app.py`（在 `/home/ubuntu/fenjing-script/`）
- **数据库**：PostgreSQL，库名 `seedance_script`，用户 `fenjing_app`，密码通过 `DB_PASSWORD` 环境变量注入
- **GitHub**：https://github.com/xingke2023/prompt-eng

---

## 文件结构

```
fenjing-script/
├── app.py                # Flask 后端，全部路由和业务逻辑
├── requirements.txt      # flask>=3.0, anthropic>=0.40
├── .env.example          # 环境变量模板
├── .gitignore
├── templates/
│   └── index.html        # 单文件前端（HTML + CSS + JS，约1600行）
└── db/
    └── init.sql          # 完整建库脚本（schema + 种子数据）
```

---

## 数据库（PostgreSQL）

库名：`seedance_script`

| 表 | 用途 |
|---|---|
| `prompts` | 每次生成/优化的记录（自动保存） |
| `favorites` | 用户手动收藏的提示词 |
| `storyboards` | 多镜头分镜脚本记录，`shots` 字段为 JSONB |
| `shot_presets` | 镜头预设库（8条内置） |
| `style_presets` | 风格预设库（8条内置） |
| `prompt_templates` | 提示词模板库（6条内置） |
| `fragments` | 素材片段库，按 `type` 分类（21条内置） |

`is_builtin=TRUE` 为内置数据，`is_builtin=FALSE` 为用户自定义。

**连接方式**：
```python
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "dbname": os.environ.get("DB_NAME", "seedance_script"),
    "user": os.environ.get("DB_USER", "fenjing_app"),
    "password": os.environ.get("DB_PASSWORD", ""),
}
```

---

## API 路由

### 提示词生成
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/generate` | 结构化生成单镜头提示词，结果存 `prompts` |
| POST | `/api/enhance` | 优化已有提示词，结果存 `prompts` |
| POST | `/api/storyboard` | 生成多镜头分镜脚本，结果存 `storyboards` |

### 历史与收藏
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/history` | 查询 `prompts` 历史，支持 `?mode=generate\|enhance&limit=N` |
| GET | `/api/history/<id>` | 获取单条完整记录 |
| GET | `/api/storyboard/history` | 分镜脚本历史 |
| GET | `/api/storyboard/<id>` | 单条分镜脚本 |
| GET/POST | `/api/favorites` | 收藏列表 / 新增收藏 |
| DELETE | `/api/favorites/<id>` | 删除收藏 |

### 素材库
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/library/shot-presets` | 镜头预设，支持 `?category=` |
| GET | `/api/library/style-presets` | 风格预设，支持 `?category=` |
| GET/POST | `/api/library/templates` | 提示词模板，支持 `?category=` |
| GET/POST | `/api/library/fragments` | 素材片段，支持 `?type=` |
| POST | `/api/library/use/<table>/<id>` | 记录使用次数（自增 `use_count`） |

---

## 前端页面（单文件 SPA）

侧边栏导航，页面通过 `switchPage(name)` 切换：

| 页面 ID | 功能 |
|---|---|
| `generate` | 结构化表单：主体/动作/场景/镜头/构图/风格/光线/色调/质量词/首末帧/时长 |
| `enhance` | 粘贴粗糙提示词 → AI 优化，返回优化后提示词+说明+标签 |
| `storyboard` | 输入视频概念+创作目标+受众+基调 → 生成多镜头分镜脚本 |
| `library` | 素材库（4个子标签：镜头预设/风格预设/模板/片段），一键填入表单 |
| `examples` | 6条内置示例，点击导入优化框 |
| `favorites` | 收藏夹管理 |
| `history` | 历史记录，点击载入优化框 |
| `guide` | 提示词写作指南（镜头词汇/构图/规则/质量词） |

---

## 核心 System Prompts（app.py）

- `SINGLE_SHOT_SYSTEM`：单镜头提示词生成，输出格式为"英文提示词 + 中文解读 + 要素标签"
- `STORYBOARD_SYSTEM`：分镜脚本生成，严格输出 JSON，每个镜头含 `shot_number / duration / shot_type / camera_move / composition / lighting / color_tone / description_zh / prompt_en / first_frame / last_frame`
- `ENHANCE_SYSTEM`：提示词优化，输出 JSON，含 `prompt / explanation / tags / composition / shot_type / camera_move`

所有 AI 调用均使用 `claude-sonnet-4-6` 模型。

---

## 提示词工程知识（项目核心）

参考了两个来源：
1. **BroderQi/Storyboard**：分镜结构（每镜头含首末帧、构图法则、创作目标、目标受众）
2. **iqinghu.com**：广告脚本结构（开头钩子 → 中段卖点 → 结尾CTA）

**高质量 Seedance 提示词结构**：
```
[镜头运动+景别] [构图法则] [主体描述] [动作] [场景环境]
[首末帧过渡] [光线色调] [视觉风格] [质量词]
```

关键规则：英文 / 镜头描述放最前 / 50-150词 / 避免否定描述 / 避免矛盾指令

---

## 开发注意事项

- 前端不引入任何外部 CDN，所有 CSS/JS 内联在 `index.html`
- API Key 由用户在页面左侧输入，存储在浏览器 `localStorage`（`apiKey` 键），也可通过 `ANTHROPIC_API_KEY` 环境变量服务端配置
- 数据库密码**不得硬编码**，必须通过环境变量注入
- `fragments` 表的 `type` 字段取值：`character / scene / action / lighting / quality / other`
- 素材库卡片点击会调用 `/api/library/use/<table>/<id>` 自增使用计数，排序权重依赖此字段
- 新增 `is_builtin=FALSE` 的用户自定义数据通过同一张表存储，前端通过绿色"自定义"标签区分
