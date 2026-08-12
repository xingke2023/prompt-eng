-- ============================================================
-- Seedance Prompt Engineering Tool — Database Migration
-- PostgreSQL 14+
-- ============================================================

-- ── Core tables ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS prompts (
    id          SERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subject     TEXT,
    action      TEXT,
    scene       TEXT,
    camera      TEXT,
    composition TEXT,
    style       TEXT,
    lighting    TEXT,
    color_tone  TEXT,
    mood        TEXT,
    quality     TEXT,
    duration    TEXT,
    first_frame TEXT,
    last_frame  TEXT,
    extra       TEXT,
    result      TEXT NOT NULL,
    mode        VARCHAR(20) NOT NULL DEFAULT 'generate',
    raw_input   TEXT,
    tokens_in   INTEGER,
    tokens_out  INTEGER
);

CREATE TABLE IF NOT EXISTS favorites (
    id          SERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    title       VARCHAR(200),
    prompt_en   TEXT NOT NULL,
    note        TEXT,
    tags        TEXT[]
);

CREATE TABLE IF NOT EXISTS storyboards (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    project_name    TEXT,
    creative_goal   TEXT,
    target_audience TEXT,
    overall_tone    TEXT,
    key_messages    TEXT,
    duration_total  TEXT,
    raw_input       TEXT,
    shots           JSONB NOT NULL DEFAULT '[]',
    tokens_in       INTEGER,
    tokens_out      INTEGER
);

-- ── Library tables ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS shot_presets (
    id             SERIAL PRIMARY KEY,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name           VARCHAR(200) NOT NULL,
    category       VARCHAR(100),
    camera_move    TEXT,
    shot_type      TEXT,
    composition    TEXT,
    lighting       TEXT,
    color_tone     TEXT,
    style          TEXT,
    quality        TEXT,
    fragment_en    TEXT,
    description_zh TEXT,
    tags           TEXT[],
    use_count      INTEGER DEFAULT 0,
    is_builtin     BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS style_presets (
    id             SERIAL PRIMARY KEY,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name           VARCHAR(200) NOT NULL,
    category       VARCHAR(100),
    style          TEXT,
    lighting       TEXT,
    color_tone     TEXT,
    quality        TEXT,
    fragment_en    TEXT,
    description_zh TEXT,
    tags           TEXT[],
    use_count      INTEGER DEFAULT 0,
    is_builtin     BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS prompt_templates (
    id             SERIAL PRIMARY KEY,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name           VARCHAR(200) NOT NULL,
    category       VARCHAR(100),
    description_zh TEXT,
    prompt_en      TEXT NOT NULL,
    subject_hint   TEXT,
    action_hint    TEXT,
    scene_hint     TEXT,
    camera         TEXT,
    composition    TEXT,
    style          TEXT,
    lighting       TEXT,
    color_tone     TEXT,
    duration       TEXT,
    tags           TEXT[],
    use_count      INTEGER DEFAULT 0,
    is_builtin     BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS fragments (
    id           SERIAL PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name         VARCHAR(200) NOT NULL,
    type         VARCHAR(50) NOT NULL,
    content_en   TEXT NOT NULL,
    content_zh   TEXT,
    tags         TEXT[],
    use_count    INTEGER DEFAULT 0,
    is_builtin   BOOLEAN DEFAULT TRUE
);

-- ── Indexes ───────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_prompts_created        ON prompts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_mode           ON prompts(mode);
CREATE INDEX IF NOT EXISTS idx_favorites_created      ON favorites(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_storyboards_created    ON storyboards(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_shot_presets_category  ON shot_presets(category);
CREATE INDEX IF NOT EXISTS idx_style_presets_category ON style_presets(category);
CREATE INDEX IF NOT EXISTS idx_templates_category     ON prompt_templates(category);
CREATE INDEX IF NOT EXISTS idx_fragments_type         ON fragments(type);

-- ── Seed: Shot Presets ────────────────────────────────────────

INSERT INTO shot_presets (name, category, camera_move, shot_type, composition, lighting, color_tone, style, quality, fragment_en, description_zh, tags) VALUES

('电影感推镜', '电影', 'slow push in', 'medium shot', 'rule of thirds',
 'golden hour sunlight', 'warm amber tones', 'cinematic, film grain', '4K, shallow depth of field',
 'Slow push-in medium shot, rule of thirds, golden hour sunlight, warm amber tones, cinematic film grain, 4K shallow depth of field',
 '经典电影推镜，黄金时刻暖光，三分法构图', ARRAY['cinematic','push in','golden hour']),

('航拍俯冲建立', '电影', 'aerial drone shot descending', 'extreme wide shot', 'centered composition',
 'soft overcast daylight', 'cool desaturated tones', 'cinematic, epic', '4K ultra-detailed',
 'Aerial drone shot descending slowly, extreme wide shot, centered composition, soft diffused daylight, cool desaturated palette, epic cinematic scale, 4K',
 '航拍俯冲建立全景，史诗感，冷色调', ARRAY['aerial','epic','establishing']),

('产品环绕特写', '商业', 'slow orbital shot 360 degrees', 'extreme close-up', 'centered composition with negative space',
 'studio three-point lighting', 'deep blacks, specular highlights', 'commercial photography style, clean', '8K ultra-detailed',
 'Slow 360-degree orbital shot, extreme close-up, centered with negative space, studio three-point lighting, specular highlights, deep black background, commercial photography, 8K',
 '产品360度环绕特写，棚拍三点布光，极致细节', ARRAY['product','orbital','studio']),

('人文跟拍纪实', '纪录片', 'handheld tracking shot', 'medium shot', 'rule of thirds',
 'natural available light', 'authentic color, slightly desaturated', 'documentary style, raw', 'natural, authentic',
 'Handheld tracking shot, medium shot, rule of thirds, natural available light, authentic slightly desaturated color, documentary style, raw and immersive',
 '手持跟拍，自然光，纪录片质感，真实感', ARRAY['handheld','documentary','authentic']),

('戏剧性仰拍', '电影', 'static shot', 'low angle shot', 'diagonal lines',
 'dramatic side lighting', 'high contrast, noir shadows', 'cinematic noir, dramatic', 'ultra-detailed',
 'Static low-angle shot, diagonal composition, dramatic side lighting, high contrast noir shadows, powerful and imposing perspective, cinematic',
 '固定仰拍，对角线构图，戏剧性侧光，黑色电影感', ARRAY['low angle','noir','dramatic']),

('柔美推镜人像', '人文', 'ultra slow push in', 'medium close-up', 'frame within frame',
 'soft diffused backlight', 'warm pastel tones, dreamy', 'soft cinematic, ethereal', 'shallow depth of field, bokeh',
 'Ultra-slow push-in to medium close-up, frame-within-frame composition, soft diffused backlight creating rim glow, warm pastel tones, dreamy bokeh background, shallow depth of field, ethereal',
 '超慢推镜人像，框中框构图，逆光晕，梦幻散景', ARRAY['portrait','dreamy','backlight']),

('上帝视角俯拍', '创意', 'slow circular orbit overhead', 'top-down bird eye view', 'symmetrical composition',
 'diffused overhead lighting', 'high saturation, graphic', 'graphic top-down, abstract', '4K ultra-clean',
 'Slow circular orbit from directly overhead, perfect top-down bird-eye view, symmetrical composition, diffused even lighting, high saturation graphic style, 4K',
 '正上方圆形轨道俯拍，对称构图，平面设计感', ARRAY['overhead','symmetry','graphic']),

('自然系升镜', '自然', 'slow crane up', 'wide shot', 'leading lines',
 'golden hour, backlit', 'warm golden, silhouette', 'nature documentary, cinematic', '4K slow motion',
 'Slow crane-up wide shot, leading lines from foreground to horizon, golden hour backlit, warm golden silhouette tones, nature documentary cinematic style, 4K smooth motion',
 '缓慢升镜全景，引导线+逆光剪影，自然纪录片感', ARRAY['crane up','nature','silhouette']);


-- ── Seed: Style Presets ───────────────────────────────────────

INSERT INTO style_presets (name, category, style, lighting, color_tone, quality, fragment_en, description_zh, tags) VALUES

('诺兰电影感', '电影',
 'IMAX cinematic, anamorphic lens flare, film grain',
 'dramatic practical lighting mixed with motivated sources',
 'desaturated teal and orange color grade',
 '4K, ultra-detailed, high contrast',
 'IMAX cinematic, anamorphic lens flare, film grain, dramatic practical lighting, desaturated teal-orange color grade, 4K high contrast',
 '诺兰风格：宽幅变形镜头、胶片颗粒、青橙色调', ARRAY['nolan','IMAX','teal-orange']),

('韦斯·安德森对称', '电影',
 'Wes Anderson style, perfectly symmetrical, pastel color palette, whimsical',
 'flat even lighting, shadowless',
 'pastel pink, yellow, mint green',
 'ultra-clean, graphic precision',
 'Wes Anderson style, perfectly symmetrical composition, flat even lighting, pastel color palette (pink, yellow, mint), whimsical graphic precision, ultra-clean',
 '韦斯安德森对称美学，粉彩色调，平面光', ARRAY['wes anderson','symmetry','pastel']),

('商业广告精品', '商业',
 'commercial advertisement style, polished, high-end brand',
 'three-point studio lighting, clean highlights',
 'rich saturated colors, clean whites',
 '8K ultra-detailed, professional, crisp',
 'Commercial advertisement style, polished high-end brand aesthetic, three-point studio lighting, rich saturated colors, clean whites, 8K ultra-crisp professional',
 '高端商业广告风格，棚拍精品感，饱和色彩', ARRAY['commercial','brand','polished']),

('复古胶片35mm', '艺术',
 'vintage 35mm film, slightly faded, grain texture',
 'natural available light, imperfect',
 'warm amber, slight color shift, faded blacks',
 'authentic film grain, soft focus edges',
 'Vintage 35mm film aesthetic, natural available light, warm amber color with slight fading, authentic film grain texture, soft focus edges, nostalgic',
 '复古35mm胶片，自然光，褪色暖调，真实颗粒感', ARRAY['vintage','35mm','nostalgic']),

('霓虹赛博朋克', '艺术',
 'cyberpunk neon aesthetic, rain-slicked streets',
 'neon signs, practical lighting, lens flares',
 'electric blue, magenta, acid green on dark backgrounds',
 'ultra-detailed, HDR, cinematic',
 'Cyberpunk neon aesthetic, rain-slicked streets, neon signs reflecting on wet surfaces, electric blue and magenta color palette, lens flares, HDR ultra-detailed',
 '赛博朋克霓虹美学，雨夜反光，蓝紫配色', ARRAY['cyberpunk','neon','rain']),

('清新日系', '生活',
 'Japanese aesthetic, soft and airy, minimal',
 'soft diffused window light, high key',
 'desaturated pastels, clean whites, soft greens',
 'gentle film grain, hazy soft focus',
 'Japanese soft aesthetic, high-key diffused window light, desaturated pastel tones, clean whites and soft greens, gentle film grain, hazy dreamy atmosphere',
 '日系清新风，高调柔光，低饱和粉彩，朦胧感', ARRAY['japanese','soft','minimal']),

('史诗大片感', '电影',
 'epic cinematic, wide angle, dramatic scale',
 'golden hour mixed with dramatic storm light',
 'warm golden contrasting with dark dramatic sky',
 'IMAX quality, HDR, ultra-wide',
 'Epic cinematic wide-angle, dramatic golden hour light battling storm clouds, warm gold contrasting dark sky, sweeping scale, IMAX quality HDR, ultra-wide perspective',
 '史诗电影感，宽幅广角，金色光线对抗暴风云', ARRAY['epic','imax','dramatic']),

('黑白艺术纪实', '艺术',
 'black and white, high contrast, artistic documentary',
 'harsh directional lighting, deep shadows',
 'pure monochrome, rich blacks, bright highlights',
 'film noir grain, ultra-detailed tonal range',
 'Black and white artistic documentary, harsh directional lighting, deep shadows and bright highlights, pure monochrome with rich tonal range, film noir grain, ultra-detailed',
 '黑白纪实艺术，强方向光，深阴影高亮，胶片颗粒', ARRAY['black white','noir','documentary']);


-- ── Seed: Prompt Templates ────────────────────────────────────

INSERT INTO prompt_templates (name, category, description_zh, prompt_en, subject_hint, action_hint, scene_hint, camera, composition, style, lighting, color_tone, duration, tags) VALUES

('人物行走城市', '人物', '适用于人物在城市场景中行走或运动的镜头',
 'Tracking shot following {subject} from behind at mid-height, rule of thirds. {subject} {action} along {scene}. Starts with figure entering frame from distance; ends with close-up of determined expression. {lighting}, cinematic film grain, {color_tone}, shallow depth of field.',
 '穿着描述+人物特征，如：a woman in a white coat, long dark hair',
 '行走动作，如：walks confidently / strides purposefully',
 '城市场景，如：a neon-lit night market street / rainy downtown sidewalk',
 'tracking shot following from behind', 'rule of thirds', 'cinematic, film grain',
 'neon reflections, night lighting', 'warm amber and cool blue', '5s', ARRAY['人物','城市','跟拍']),

('产品英雄镜头', '产品', '产品主角特写展示，适用于广告和电商',
 'Slow {camera} of {subject} on {scene}. Starts with product partially revealed; ends with full product in perfect focus. {lighting}, revealing every detail and texture. {color_tone}, commercial photography style, {quality}.',
 '产品名称+材质，如：a glass perfume bottle / leather handbag',
 '展示动作（通常由镜头完成，主体静止）',
 '背景/展台，如：black velvet surface / marble pedestal',
 'orbital shot 180 degrees', 'centered with negative space', 'commercial photography, ultra-clean',
 'studio three-point lighting, soft boxes', 'deep blacks, rich product colors', NULL, ARRAY['产品','商业','特写']),

('自然风景建立镜', '风景', '建立自然场景的大景别镜头，适合开场或过场',
 '{camera} over {scene}. {action}. Starts with a distant view; ends with intimate environment detail. {lighting}, nature documentary cinematic style, {color_tone}, 4K ultra-detailed.',
 '可留空，以场景为主体',
 '自然现象描述，如：clouds drift slowly across the sky / waves roll in rhythmically',
 '自然地点，如：vast lavender fields at sunrise / misty mountain valley',
 'slow crane up', 'leading lines', 'nature documentary, cinematic',
 'golden hour sunlight', 'warm golden and soft green tones', '8s', ARRAY['风景','自然','建立镜']),

('广告三幕结构', '广告', '开头钩子+中段产品+结尾CTA的完整广告结构',
 'HOOK: {hook_shot}. MIDDLE: {product_shot}, showcasing {key_feature}. CTA: Close-up of {cta_element} with brand reveal. Throughout: {lighting}, {style}, {color_tone}.',
 '品牌/产品名称',
 '核心卖点展示动作',
 '产品使用场景',
 'varied: wide establishing + tracking + close-up', 'rule of thirds throughout',
 'commercial polished, high-end', 'professional studio lighting', 'brand colors, clean and vibrant',
 NULL, ARRAY['广告','三幕','商业']),

('人像情绪特写', '人物', '聚焦人物情感和表情的近景特写',
 'Ultra-slow push-in from medium to extreme close-up, {composition}. {subject} {action}. Starts with {subject} small in frame surrounded by environment; ends with eyes filling the frame, emotion visible in every detail. {lighting}, {style}, {color_tone}.',
 '人物描述，如：an elderly fisherman with weathered face',
 '情感动作，如：gazes at the horizon / closes eyes slowly',
 '环境，如：against golden sunset / in dim candlelight',
 'ultra-slow push in to ECU', 'frame within frame', 'cinematic, shallow depth of field',
 'soft diffused sidelight', 'warm desaturated, emotional', '8s', ARRAY['人像','情绪','特写']),

('街头人文纪实', '人文', '街头纪实风格，真实生活片段',
 'Handheld medium shot, {composition}, candid documentary style. {subject} {action} in {scene}. Natural available light spilling through environment. Authentic motion, slightly imperfect framing, real-world texture. {color_tone}, 35mm documentary grain.',
 '街头人物，如：an old man selling tea / children playing',
 '日常动作，如：laughs and gestures / haggling at a market stall',
 '真实场景，如：a busy morning market / narrow alleyway',
 'handheld medium shot', 'rule of thirds, candid', 'documentary, 35mm film',
 'natural available light', 'authentic slightly desaturated', NULL, ARRAY['纪实','人文','街头']);


-- ── Seed: Fragments ───────────────────────────────────────────

INSERT INTO fragments (name, type, content_en, content_zh, tags) VALUES

-- Characters
('商务精英女性', 'character',
 'a confident businesswoman in a tailored charcoal blazer, sharp eyes, hair pulled back neatly',
 '自信商务女性，深灰西装，利落发型', ARRAY['商务','女性']),
('年轻男性艺术家', 'character',
 'a young male artist in paint-stained linen shirt, expressive hands, thoughtful gaze',
 '年轻男性艺术家，沾颜料亚麻衬衫，若有所思', ARRAY['艺术','男性']),
('老渔夫', 'character',
 'a weathered old fisherman with deep-set eyes, sun-darkened skin, and calloused hands',
 '饱经风霜的老渔夫，深邃眼神，粗糙大手', ARRAY['老人','纪实']),
('优雅女性', 'character',
 'an elegant woman in flowing silk dress, graceful movements, serene expression',
 '优雅女性，飘逸丝质长裙，从容姿态', ARRAY['优雅','女性']),
('儿童奔跑', 'character',
 'a joyful child in bright yellow raincoat, laughing and jumping through puddles',
 '快乐小孩，明黄雨衣，踩水坑欢笑', ARRAY['儿童','活力']),

-- Scenes
('日本京都小巷', 'scene',
 'narrow cobblestone alley in Kyoto, wooden machiya townhouses on both sides, paper lanterns hanging overhead',
 '京都石板小巷，两侧木质町屋，纸灯笼悬挂', ARRAY['日本','京都','城市']),
('热带雨林', 'scene',
 'dense tropical rainforest with towering canopy, shafts of light piercing through leaves, mist-covered ground',
 '热带雨林，巨大树冠，光线穿透叶片，雾气弥漫', ARRAY['自然','森林','雾']),
('现代极简办公室', 'scene',
 'minimalist modern office with floor-to-ceiling glass windows, white surfaces, city view below',
 '极简现代办公室，落地玻璃，白色空间，城市俯瞰', ARRAY['商业','室内','极简']),
('夜市街头', 'scene',
 'vibrant night market with colorful food stalls, crowds of people, steam rising from woks',
 '夜市街头，彩色摊位，人流涌动，炒锅蒸气', ARRAY['夜市','街头','亚洲']),
('荒漠盐湖', 'scene',
 'endless salt flat desert with mirror-like water reflection, pink and orange sky',
 '荒漠盐湖，镜面水面倒影，粉橙色天空', ARRAY['沙漠','盐湖','壮阔']),

-- Actions
('缓慢转身', 'action',
 'turns slowly to face the camera, a subtle smile forming at the corner of their lips',
 '缓慢转身面向镜头，嘴角微微上扬', ARRAY['转身','情绪']),
('走向远方', 'action',
 'walks steadily toward the horizon, silhouetted against the fading light, never looking back',
 '走向地平线，逆光剪影，从不回头', ARRAY['行走','剪影']),
('抚摸产品', 'action',
 'gently runs fingertips along the surface, appreciating every texture and detail',
 '指尖轻抚表面，感受每一处质感细节', ARRAY['产品','触摸']),
('仰望天空', 'action',
 'tilts head back slowly, eyes closed, breathing deeply, a moment of complete stillness',
 '缓缓仰头，闭眼，深呼吸，片刻静止', ARRAY['情绪','宁静']),

-- Lighting
('丁达尔光效', 'lighting',
 'dramatic Tyndall effect shafts of light piercing through dust particles in a dark interior',
 '丁达尔效应光束穿透暗室尘埃颗粒', ARRAY['光效','戏剧']),
('窗边柔光', 'lighting',
 'soft diffused north window light, wrapping gently around the subject with minimal shadows',
 '北向柔和窗边散射光，柔和包裹主体，阴影极少', ARRAY['柔光','室内']),
('雨后反光', 'lighting',
 'wet streets reflecting city lights in abstract colorful puddles and rivers of light',
 '湿润街道映出城市灯光，彩色水坑光影流动', ARRAY['反光','雨后','夜晚']),
('蜡烛暖光', 'lighting',
 'warm flickering candlelight casting dancing shadows, intimate and warm',
 '温暖摇曳烛光，跳动阴影，亲密暖意', ARRAY['烛光','暖调']),

-- Quality
('电影最高质量', 'quality',
 'IMAX cinematic quality, anamorphic 2.39:1 aspect ratio, film grain, 4K HDR, ultra-detailed',
 'IMAX电影级，变形镜头比例，胶片颗粒，4K HDR', ARRAY['电影','最高质量']),
('商业精品质量', 'quality',
 'commercial grade, ultra-sharp, 8K resolution, professional color grading, pristine clean',
 '商业级精品，超锐利，8K分辨率，专业调色', ARRAY['商业','8K']),
('慢动作高帧', 'quality',
 'ultra slow motion 240fps equivalent, silky smooth, every detail frozen in time',
 '超慢动作240帧等效，丝滑流畅，时间凝固', ARRAY['慢动作','高帧']);
