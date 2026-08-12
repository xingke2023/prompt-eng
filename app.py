import os
import json
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, jsonify
import anthropic

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5432)),
    "dbname":   os.environ.get("DB_NAME", "seedance_script"),
    "user":     os.environ.get("DB_USER", "fenjing_app"),
    "password": os.environ.get("DB_PASSWORD", ""),
}


def get_db():
    return psycopg2.connect(**DB_CONFIG)


def get_client(api_key):
    return anthropic.Anthropic(api_key=api_key)


# ── System prompts ─────────────────────────────────────────────────────────────

SINGLE_SHOT_SYSTEM = """你是专业的 Seedance 视频提示词专家，精通电影分镜语言。根据用户提供的要素生成高质量英文提示词。

## 提示词结构（按顺序）
[镜头运动+景别] + [构图法则] + [主体描述] + [动作] + [场景环境] + [首末帧过渡] + [光线色调] + [视觉风格] + [质量词]

## 镜头语言
- 运动：static / slow push in / pull back / pan / tracking / orbital / crane up / handheld / aerial
- 景别：ECU / CU / MCU / medium shot / wide shot / EWS / bird's eye / low angle

## 构图法则（Composition）
- rule of thirds（三分法）
- symmetrical composition（对称构图）
- golden ratio / spiral（黄金比例）
- centered composition（中心构图）
- diagonal lines（对角线构图）
- leading lines（引导线构图）
- frame within frame（框中框）
- negative space（留白）

## 色调控制
- warm tones (amber, golden) / cool tones (blue, teal) / high contrast / desaturated / pastel / neon

## 首末帧
- starts with ... / ends with ...（描述画面起始和结束状态，形成叙事弧）

## 时长暗示
- 3s: 单一简洁动作  5s: 有起伏的运动  8-10s: 完整叙事弧

## 写作规则
1. 英文，具体不抽象
2. 镜头/构图描述放最前
3. 50-150词
4. 避免 no/without 否定
5. 避免矛盾指令

## 输出格式

**英文提示词：**
（直接输出，不加引号）

**中文解读：**
（2-3句设计思路）

**要素标签：**
（逗号分隔）"""


QCZH_SYSTEM = """你是专业的影视导演和分镜脚本师，精通中国古典叙事结构**起承转合**，同时掌握 Seedance 视频提示词。

## 起承转合四段结构

### 起（Opening）— 建立，蓄势
- **镜头任务**：交代时间/地点/主体，情绪中性，观众在问"这是哪里？这是谁？"
- **镜头语言**：大景别（WS/EWS），固定或缓慢升/拉，主体小
- **构图**：三分法，主体偏角，留大量环境空间
- **节奏**：慢，呼吸感，不急于展示
- **时长**：4-6s

### 承（Development）— 推进，投入
- **镜头任务**：跟近主体，展开行动/细节，建立情感投入，观众开始在意
- **镜头语言**：景别推进（MS/MCU），跟拍或推镜，主体变大
- **构图**：三分法或框中框，比"起"更亲近
- **节奏**：有运动感，有温度
- **时长**：4-6s

### 转（Turn）— 转折，记忆点 ⚡ 最关键
- **镜头任务**：打破前面建立的情绪节奏，制造意外/反转/揭示，这是全片记忆点
- **原则**：与"承"形成强烈对比——景别相反（承是MCU则转用EWS）、情绪相反、光线相反
- **镜头语言**：极端景别（ECU或EWS）、突然静止或突然运动、视角颠覆
- **构图**：故意打破之前的构图规则
- **节奏**：节拍感强，冲击力
- **时长**：2-4s（短促有力）

### 合（Resolution）— 收束，余韵
- **镜头任务**：呼应"起"的构图，但含义已完全不同；留白，让观众自己填满情感
- **原则**："形回意不回"——画面回到起的格局，但观众心境已变
- **镜头语言**：回到大景别，缓慢淡出或静止定格
- **构图**：刻意呼应"起"的构图
- **节奏**：渐慢，留空
- **时长**：5-8s

---

## 每个镜头输出字段

```json
{
  "shot_number": 1,
  "phase": "起",           // 起 / 承 / 转 / 合
  "phase_en": "Opening",  // Opening / Development / Turn / Resolution
  "phase_role": "建立场景，交代环境与主体",  // 这个镜头在叙事中的具体任务
  "duration": "5s",
  "shot_type": "WS",
  "camera_move": "slow pull back",
  "composition": "rule of thirds, subject small in frame",
  "lighting": "...",
  "color_tone": "...",
  "description_zh": "一句话说明",
  "prompt_en": "完整英文提示词（50-120词）",
  "first_frame": "首帧中文描述",
  "last_frame": "末帧中文描述",
  "contrast_with": ""  // 仅"转"填写：与哪个前序镜头形成对比，如何对比
}
```

## 总体输出 JSON

```json
{
  "title": "脚本标题",
  "narrative_structure": "起承转合",
  "total_duration": "约XX秒",
  "narrative_summary": "叙事思路（重点解释转折点的设计）",
  "phase_breakdown": {
    "起": "第1-X镜：...",
    "承": "第X-X镜：...",
    "转": "第X镜：...",
    "合": "第X-X镜：..."
  },
  "shots": [ ... ]
}
```

严格输出 JSON，不要其他内容。转折点镜头是最重要的，设计时要大胆，与前序镜头形成强烈反差。"""

STORYBOARD_SYSTEM = """你是专业的影视导演和分镜脚本师，同时精通 Seedance 视频生成提示词。

根据用户的视频创作需求，生成完整的多镜头分镜脚本。每个镜头都包含可直接用于 Seedance 的英文提示词。

## 分镜设计原则（来自专业影视制作）

### 叙事结构
- **开头钩子**（Hook）：前1-2个镜头抓住注意力，建立情境
- **中段发展**：展开主要内容，景别从大到小或形成节奏对比
- **结尾收束**：呼应开头或留下印象，可用全景或特写收尾

### 镜头节奏
- 动静结合：运动镜头与固定镜头交替使用
- 景别变化：大景别建立空间感，小景别聚焦情感
- 构图呼应：相邻镜头构图形成对话

### 每个镜头必须包含
1. **shot_number**：镜头编号
2. **duration**：时长（"3s"/"5s"/"8s"/"10s"）
3. **shot_type**：景别（ECU/CU/MCU/MS/WS/EWS）
4. **camera_move**：镜头运动
5. **composition**：构图法则
6. **lighting**：光线描述
7. **color_tone**：色调
8. **description_zh**：中文镜头说明（1句）
9. **prompt_en**：Seedance 英文提示词（50-120词，可直接使用）
10. **first_frame**：首帧画面描述（中文，1句）
11. **last_frame**：末帧画面描述（中文，1句）

## 输出格式

严格输出 JSON，不要其他内容：
{
  "title": "脚本标题",
  "total_duration": "总时长估算",
  "narrative_summary": "叙事思路（2-3句中文）",
  "shots": [
    {
      "shot_number": 1,
      "duration": "5s",
      "shot_type": "WS",
      "camera_move": "slow push in",
      "composition": "rule of thirds",
      "lighting": "golden hour sunlight",
      "color_tone": "warm amber tones",
      "description_zh": "建立场景，交代环境",
      "prompt_en": "Slow push-in wide shot, rule of thirds composition. ...",
      "first_frame": "远景全景，人物在左侧三分之一处",
      "last_frame": "推进至中景，人物居中，背景虚化"
    }
  ]
}"""


ENHANCE_SYSTEM = """你是 Seedance 视频提示词优化专家，掌握专业分镜语言。

优化原则（来自影视制作规范）：
1. 补充镜头语言（景别+运动，放最前）
2. 加入构图法则（rule of thirds / symmetry / diagonal lines 等）
3. 补充色调控制词
4. 增强动作动词的精准度
5. 加入首末帧过渡描述（starts with ... / ends with ...）
6. 控制在 80-150 词

输出 JSON（只输出JSON）：
{
  "prompt": "优化后英文提示词",
  "explanation": "优化点说明（中文，2-3句）",
  "tags": ["标签1", "标签2", "标签3"],
  "composition": "使用的构图法则",
  "shot_type": "景别",
  "camera_move": "镜头运动"
}"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate_prompt():
    data = request.json
    api_key = data.get("api_key", "") or ANTHROPIC_API_KEY
    if not api_key:
        return jsonify({"error": "请在左侧填入 API Key"}), 400

    subject     = data.get("subject", "").strip()
    action      = data.get("action", "").strip()
    scene       = data.get("scene", "").strip()
    camera      = data.get("camera", "").strip()
    composition = data.get("composition", "").strip()
    style       = data.get("style", "").strip()
    lighting    = data.get("lighting", "").strip()
    color_tone  = data.get("color_tone", "").strip()
    mood        = data.get("mood", "").strip()
    quality     = data.get("quality", "").strip()
    duration    = data.get("duration", "").strip()
    first_frame = data.get("first_frame", "").strip()
    last_frame  = data.get("last_frame", "").strip()
    extra       = data.get("description", "").strip()

    if not subject and not action:
        return jsonify({"error": "请填写主体描述或动作"}), 400

    parts = []
    if subject:     parts.append(f"主体：{subject}")
    if action:      parts.append(f"动作：{action}")
    if scene:       parts.append(f"场景：{scene}")
    if camera:      parts.append(f"镜头：{camera}")
    if composition: parts.append(f"构图：{composition}")
    if style:       parts.append(f"视觉风格：{style}")
    if lighting:    parts.append(f"光线：{lighting}")
    if color_tone:  parts.append(f"色调：{color_tone}")
    if mood:        parts.append(f"氛围：{mood}")
    if quality:     parts.append(f"质量词：{quality}")
    if duration:    parts.append(f"时长：{duration}")
    if first_frame: parts.append(f"首帧：{first_frame}")
    if last_frame:  parts.append(f"末帧：{last_frame}")
    if extra:       parts.append(f"补充：{extra}")

    try:
        client = get_client(api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SINGLE_SHOT_SYSTEM,
            messages=[{"role": "user", "content": "生成 Seedance 提示词：\n\n" + "\n".join(parts)}],
        )
        result = response.content[0].text
        tokens_in, tokens_out = response.usage.input_tokens, response.usage.output_tokens

        try:
            with get_db() as conn, conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO prompts
                        (subject, action, scene, camera, composition, style, lighting,
                         color_tone, mood, quality, duration, first_frame, last_frame,
                         extra, result, mode, tokens_in, tokens_out)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'generate',%s,%s)
                    RETURNING id
                """, (subject, action, scene, camera, composition, style, lighting,
                      color_tone, mood, quality, duration, first_frame, last_frame,
                      extra, result, tokens_in, tokens_out))
                prompt_id = cur.fetchone()[0]
        except Exception as e:
            prompt_id = None
            app.logger.warning(f"DB save failed: {e}")

        return jsonify({"result": result, "id": prompt_id,
                        "usage": {"input": tokens_in, "output": tokens_out}})

    except anthropic.AuthenticationError:
        return jsonify({"error": "API Key 无效，请检查"}), 401
    except anthropic.RateLimitError:
        return jsonify({"error": "请求过于频繁，请稍后重试"}), 429
    except Exception as e:
        return jsonify({"error": f"生成失败：{str(e)}"}), 500


@app.route("/api/enhance", methods=["POST"])
def enhance_prompt():
    data = request.json
    raw_prompt = data.get("prompt", "").strip()
    if not raw_prompt:
        return jsonify({"error": "请输入需要优化的提示词"}), 400

    api_key = data.get("api_key", "") or ANTHROPIC_API_KEY
    if not api_key:
        return jsonify({"error": "请在左侧填入 API Key"}), 400

    try:
        client = get_client(api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=ENHANCE_SYSTEM,
            messages=[{"role": "user", "content": f"优化：{raw_prompt}"}],
        )
        tokens_in, tokens_out = response.usage.input_tokens, response.usage.output_tokens
        try:
            parsed = parse_json_response(response.content[0].text)
        except Exception:
            parsed = {"prompt": response.content[0].text, "explanation": "", "tags": []}

        try:
            with get_db() as conn, conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO prompts (raw_input, result, mode, tokens_in, tokens_out)
                    VALUES (%s,%s,'enhance',%s,%s) RETURNING id
                """, (raw_prompt, parsed.get("prompt", ""), tokens_in, tokens_out))
                prompt_id = cur.fetchone()[0]
        except Exception as e:
            prompt_id = None
            app.logger.warning(f"DB save failed: {e}")

        return jsonify({"result": parsed, "id": prompt_id,
                        "usage": {"input": tokens_in, "output": tokens_out}})

    except anthropic.AuthenticationError:
        return jsonify({"error": "API Key 无效"}), 401
    except anthropic.RateLimitError:
        return jsonify({"error": "请求过于频繁，请稍后重试"}), 429
    except Exception as e:
        return jsonify({"error": f"优化失败：{str(e)}"}), 500


@app.route("/api/storyboard", methods=["POST"])
def generate_storyboard():
    data = request.json
    api_key = data.get("api_key", "") or ANTHROPIC_API_KEY
    if not api_key:
        return jsonify({"error": "请在左侧填入 API Key"}), 400

    concept              = data.get("concept", "").strip()
    creative_goal        = data.get("creative_goal", "").strip()
    target_audience      = data.get("target_audience", "").strip()
    overall_tone         = data.get("overall_tone", "").strip()
    key_messages         = data.get("key_messages", "").strip()
    shot_count           = data.get("shot_count", 5)
    duration_total       = data.get("duration_total", "").strip()
    project_name         = data.get("project_name", "").strip()
    narrative_structure  = data.get("narrative_structure", "free")  # "free" | "qczh"

    if not concept:
        return jsonify({"error": "请输入视频概念描述"}), 400

    parts = [f"视频概念：{concept}"]
    if creative_goal:   parts.append(f"创作目标：{creative_goal}")
    if target_audience: parts.append(f"目标受众：{target_audience}")
    if overall_tone:    parts.append(f"整体基调：{overall_tone}")
    if key_messages:    parts.append(f"核心信息：{key_messages}")
    if duration_total:  parts.append(f"总时长：{duration_total}")

    if narrative_structure == "qczh":
        # 起承转合：镜头数固定逻辑 起1-2 承1-2 转1 合1-2
        qczh_count = max(4, int(shot_count))
        parts.append(f"总镜头数：{qczh_count}个（按起承转合四段分配，其中'转'只有1个镜头）")
        system_prompt = QCZH_SYSTEM
        user_msg = "请用起承转合结构生成分镜脚本：\n\n" + "\n".join(parts)
    else:
        parts.append(f"镜头数量：{shot_count}个镜头")
        system_prompt = STORYBOARD_SYSTEM
        user_msg = "\n".join(parts)

    try:
        client = get_client(api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        tokens_in, tokens_out = response.usage.input_tokens, response.usage.output_tokens

        try:
            storyboard = parse_json_response(response.content[0].text)
        except Exception as e:
            return jsonify({"error": f"解析分镜结果失败：{str(e)}", "raw": response.content[0].text}), 500

        storyboard["narrative_structure"] = narrative_structure

        try:
            with get_db() as conn, conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO storyboards
                        (project_name, creative_goal, target_audience, overall_tone,
                         key_messages, duration_total, raw_input, shots,
                         narrative_structure, tokens_in, tokens_out)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
                """, (project_name or storyboard.get("title", ""),
                      creative_goal, target_audience, overall_tone,
                      key_messages, storyboard.get("total_duration", duration_total),
                      concept, json.dumps(storyboard.get("shots", []), ensure_ascii=False),
                      narrative_structure, tokens_in, tokens_out))
                sb_id = cur.fetchone()[0]
        except Exception as e:
            sb_id = None
            app.logger.warning(f"DB save failed: {e}")

        return jsonify({"result": storyboard, "id": sb_id,
                        "usage": {"input": tokens_in, "output": tokens_out}})

    except anthropic.AuthenticationError:
        return jsonify({"error": "API Key 无效"}), 401
    except anthropic.RateLimitError:
        return jsonify({"error": "请求过于频繁，请稍后重试"}), 429
    except Exception as e:
        return jsonify({"error": f"分镜生成失败：{str(e)}"}), 500


@app.route("/api/storyboard/history", methods=["GET"])
def storyboard_history():
    limit = min(int(request.args.get("limit", 20)), 100)
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, created_at, project_name, creative_goal, duration_total,
                       raw_input, tokens_in, tokens_out,
                       jsonb_array_length(shots) AS shot_count
                FROM storyboards ORDER BY created_at DESC LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/storyboard/<int:sb_id>", methods=["GET"])
def get_storyboard(sb_id):
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM storyboards WHERE id = %s", (sb_id,))
            row = cur.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        d = dict(row)
        if isinstance(d.get("shots"), str):
            d["shots"] = json.loads(d["shots"])
        return jsonify(d)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/favorites", methods=["GET"])
def list_favorites():
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM favorites ORDER BY created_at DESC LIMIT 100")
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    data = request.json
    prompt_en = data.get("prompt_en", "").strip()
    if not prompt_en:
        return jsonify({"error": "提示词不能为空"}), 400
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO favorites (title, prompt_en, note, tags)
                VALUES (%s,%s,%s,%s) RETURNING id, created_at
            """, (data.get("title") or None, prompt_en,
                  data.get("note") or None, data.get("tags", [])))
            row = cur.fetchone()
        return jsonify({"id": row[0], "created_at": str(row[1])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/favorites/<int:fav_id>", methods=["DELETE"])
def delete_favorite(fav_id):
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM favorites WHERE id = %s", (fav_id,))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    mode  = request.args.get("mode", "")
    limit = min(int(request.args.get("limit", 20)), 100)
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if mode:
                cur.execute("""
                    SELECT id, created_at, mode, subject, action, scene, raw_input,
                           left(result, 300) AS result_preview, tokens_in, tokens_out
                    FROM prompts WHERE mode = %s ORDER BY created_at DESC LIMIT %s
                """, (mode, limit))
            else:
                cur.execute("""
                    SELECT id, created_at, mode, subject, action, scene, raw_input,
                           left(result, 300) AS result_preview, tokens_in, tokens_out
                    FROM prompts ORDER BY created_at DESC LIMIT %s
                """, (limit,))
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/<int:prompt_id>", methods=["GET"])
def get_history_item(prompt_id):
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM prompts WHERE id = %s", (prompt_id,))
            row = cur.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return jsonify(dict(row))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/examples", methods=["GET"])
def get_examples():
    return jsonify([
        {
            "title": "城市夜景行走",
            "category": "人物",
            "prompt": "Tracking shot following from behind at mid-height, rule of thirds composition. A stylish woman in a red trench coat strides confidently along a rain-soaked city street at night. Starts with her silhouette entering frame; ends with neon reflections filling the foreground. Warm amber and cool blue tones, cinematic, film grain, shallow depth of field.",
            "zh": "时尚女性雨夜都市行走，跟拍+三分法，首末帧过渡，霓虹反光"
        },
        {
            "title": "麦田风暴云景",
            "category": "风景",
            "prompt": "Static locked-off shot, low angle, diagonal lines composition. Golden wheat fields sway under dramatic storm clouds. Starts with calm field; ends with first raindrops hitting the grain. Shafts of sunlight break through dark clouds. Slow motion, epic cinematic, warm golden mixed with dark storm, 4K ultra-detailed.",
            "zh": "麦田风暴，仰角固定+对角线构图，首帧宁静末帧雨至"
        },
        {
            "title": "奢华手表特写",
            "category": "产品",
            "prompt": "Extreme close-up, slow 180-degree orbital shot, centered composition with negative space. A luxury watch rests on dark velvet. Starts with dial face centered; ends with side profile revealing the clasp. Studio three-point lighting, specular highlights on metal case, deep blacks, 8K ultra-detailed, commercial photography.",
            "zh": "手表ECU环绕，中心+留白构图，棚拍三点光，首末帧展示不同角度"
        },
        {
            "title": "产品广告三镜头",
            "category": "广告",
            "prompt": "Shot 1 — Slow push-in wide shot establishing the scene. Shot 2 — Tracking medium shot following the product hero. Shot 3 — Extreme close-up static reveal. Warm golden hour, rule of thirds throughout, cinematic color grading, commercial style.",
            "zh": "广告三镜头结构：建立全景→跟拍中景→特写揭示"
        },
        {
            "title": "海浪冲击礁石",
            "category": "自然",
            "prompt": "Low angle shot at water level, leading lines from rocks to horizon. Powerful ocean waves crash against volcanic rocks. Starts with calm ocean surface reflecting sky; ends with massive spray arc frozen mid-air. Overcast sky, desaturated cool tones, documentary raw style, 240fps slow motion equivalent.",
            "zh": "水面低角度+引导线构图，首帧宁静末帧浪花冻结"
        },
        {
            "title": "咖啡馆晨光阅读",
            "category": "生活",
            "prompt": "Slow push-in from wide to medium close-up, rule of thirds, frame-within-frame (window framing subject). A young man in glasses reads at a café table. Starts with him small in frame, surrounded by warm morning light; ends with his face filling the frame, eyes reflecting page text. Bokeh background, nostalgic 35mm film aesthetic.",
            "zh": "推镜+三分法+框中框构图，首末帧叙事弧，胶片感"
        }
    ])


# ── Library APIs ──────────────────────────────────────────────────────────────

@app.route("/api/library/shot-presets", methods=["GET"])
def get_shot_presets():
    category = request.args.get("category", "")
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if category:
                cur.execute("SELECT * FROM shot_presets WHERE category=%s ORDER BY use_count DESC, id", (category,))
            else:
                cur.execute("SELECT * FROM shot_presets ORDER BY category, id")
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/style-presets", methods=["GET"])
def get_style_presets():
    category = request.args.get("category", "")
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if category:
                cur.execute("SELECT * FROM style_presets WHERE category=%s ORDER BY use_count DESC, id", (category,))
            else:
                cur.execute("SELECT * FROM style_presets ORDER BY category, id")
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/templates", methods=["GET"])
def get_templates():
    category = request.args.get("category", "")
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if category:
                cur.execute("SELECT * FROM prompt_templates WHERE category=%s ORDER BY use_count DESC, id", (category,))
            else:
                cur.execute("SELECT * FROM prompt_templates ORDER BY category, id")
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/templates", methods=["POST"])
def save_template():
    data = request.json
    if not data.get("name") or not data.get("prompt_en"):
        return jsonify({"error": "名称和提示词不能为空"}), 400
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO prompt_templates
                    (name, category, description_zh, prompt_en, subject_hint, action_hint,
                     scene_hint, camera, composition, style, lighting, color_tone, duration, tags, is_builtin)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE) RETURNING id
            """, (data["name"], data.get("category","自定义"), data.get("description_zh",""),
                  data["prompt_en"], data.get("subject_hint",""), data.get("action_hint",""),
                  data.get("scene_hint",""), data.get("camera",""), data.get("composition",""),
                  data.get("style",""), data.get("lighting",""), data.get("color_tone",""),
                  data.get("duration",""), data.get("tags",[])))
            row = cur.fetchone()
        return jsonify({"id": row[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/fragments", methods=["GET"])
def get_fragments():
    ftype = request.args.get("type", "")
    try:
        with get_db() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if ftype:
                cur.execute("SELECT * FROM fragments WHERE type=%s ORDER BY use_count DESC, id", (ftype,))
            else:
                cur.execute("SELECT * FROM fragments ORDER BY type, id")
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/fragments", methods=["POST"])
def save_fragment():
    data = request.json
    if not data.get("name") or not data.get("content_en"):
        return jsonify({"error": "名称和英文内容不能为空"}), 400
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fragments (name, type, content_en, content_zh, tags, is_builtin)
                VALUES (%s,%s,%s,%s,%s,FALSE) RETURNING id
            """, (data["name"], data.get("type","other"), data["content_en"],
                  data.get("content_zh",""), data.get("tags",[])))
            row = cur.fetchone()
        return jsonify({"id": row[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/use/<string:table>/<int:item_id>", methods=["POST"])
def record_use(table, item_id):
    allowed = {"shot_presets", "style_presets", "prompt_templates", "fragments"}
    if table not in allowed:
        return jsonify({"error": "invalid table"}), 400
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute(f"UPDATE {table} SET use_count = use_count + 1 WHERE id = %s", (item_id,))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── 港险案例库 APIs ────────────────────────────────────────────────────────────

@app.route("/api/cases", methods=["GET"])
def get_cases():
    """List insurance cases with optional tag/search filter + pagination."""
    try:
        tag     = request.args.get("tag", "").strip()
        search  = request.args.get("search", "").strip()
        featured_only = request.args.get("featured", "").lower() == "true"
        page    = max(1, int(request.args.get("page", 1)))
        limit   = min(50, max(1, int(request.args.get("limit", 20))))
        offset  = (page - 1) * limit

        conditions = []
        params = []
        if featured_only:
            conditions.append("is_featured = TRUE")
        if tag:
            conditions.append("%s = ANY(tags)")
            params.append(tag)
        if search:
            conditions.append("(title ILIKE %s OR description ILIKE %s OR insurance_needs ILIKE %s)")
            params += [f"%{search}%", f"%{search}%", f"%{search}%"]

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"SELECT COUNT(*) FROM insurance_cases {where}", params)
                total = cur.fetchone()["count"]
                cur.execute(f"""
                    SELECT id, source_id, title, tags, customer_age,
                           family_structure, insurance_needs,
                           LEFT(description, 300) AS description_preview,
                           budget_suggestion, is_featured, sort_order, created_at
                    FROM insurance_cases {where}
                    ORDER BY is_featured DESC, sort_order, id
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])
                rows = cur.fetchall()
        return jsonify({"success": True, "total": total, "page": page,
                        "limit": limit, "results": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cases/<int:case_id>", methods=["GET"])
def get_case(case_id):
    """Get full detail of a single insurance case."""
    try:
        with get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM insurance_cases WHERE id = %s", (case_id,))
                row = cur.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"success": True, "data": dict(row)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cases/tags", methods=["GET"])
def get_case_tags():
    """Return all tags used in insurance_cases with counts."""
    try:
        with get_db() as db:
            with db.cursor() as cur:
                cur.execute("SELECT UNNEST(tags) AS tag FROM insurance_cases")
                rows = cur.fetchall()
        counts = {}
        for (tag,) in rows:
            if tag:
                counts[tag] = counts.get(tag, 0) + 1
        tag_list = sorted(counts.items(), key=lambda x: -x[1])
        return jsonify({"success": True, "tags": [{"name": t, "count": c} for t, c in tag_list]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/qa", methods=["GET"])
def get_qa():
    """List HK insurance Q&As with optional tag/search filter + pagination."""
    try:
        tag    = request.args.get("tag", "").strip()
        search = request.args.get("search", "").strip()
        page   = max(1, int(request.args.get("page", 1)))
        limit  = min(50, max(1, int(request.args.get("limit", 20))))
        offset = (page - 1) * limit

        conditions = []
        params = []
        if tag:
            conditions.append("%s = ANY(tags)")
            params.append(tag)
        if search:
            conditions.append("(title ILIKE %s OR content ILIKE %s)")
            params += [f"%{search}%", f"%{search}%"]

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"SELECT COUNT(*) FROM insurance_qa {where}", params)
                total = cur.fetchone()["count"]
                cur.execute(f"""
                    SELECT id, source_id, title, tags,
                           LEFT(content, 300) AS content_preview,
                           sort_order, created_at
                    FROM insurance_qa {where}
                    ORDER BY sort_order, id
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])
                rows = cur.fetchall()
        return jsonify({"success": True, "total": total, "page": page,
                        "limit": limit, "results": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/qa/<int:qa_id>", methods=["GET"])
def get_qa_detail(qa_id):
    """Get full content of a single Q&A."""
    try:
        with get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM insurance_qa WHERE id = %s", (qa_id,))
                row = cur.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"success": True, "data": dict(row)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/qa/tags", methods=["GET"])
def get_qa_tags():
    """Return all tags used in insurance_qa with counts."""
    try:
        with get_db() as db:
            with db.cursor() as cur:
                cur.execute("SELECT UNNEST(tags) AS tag FROM insurance_qa")
                rows = cur.fetchall()
        counts = {}
        for (tag,) in rows:
            if tag:
                counts[tag] = counts.get(tag, 0) + 1
        tag_list = sorted(counts.items(), key=lambda x: -x[1])
        return jsonify({"success": True, "tags": [{"name": t, "count": c} for t, c in tag_list]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8129)
