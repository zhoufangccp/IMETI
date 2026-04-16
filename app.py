import streamlit as st
import json
import os
import textwrap
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ================= 1. 页面基本配置 =================
st.set_page_config(page_title="IMETI", layout="centered", page_icon="🧬")


# ================= 2. 读取配置 & 动态计算最高分 =================
@st.cache_data
def load_questions():
    with open('questionss.json', 'r', encoding='utf-8') as f:
        return json.load(f)


QUESTIONS = load_questions()


# 【新增核心逻辑】：动态计算每个人格理论上的最高可能得分
@st.cache_data
def calculate_max_scores(questions):
    max_scores = {}
    for q in questions:
        if q.get("type") == "multiple":
            # 多选题：用户理论上可以全选，所以把所有选项的分数都加上
            for opt in q["options"]:
                t = opt["target_type"]
                max_scores[t] = max_scores.get(t, 0) + opt["score"]
        else:
            # 单选题：用户只能选一个，所以某个人格在这道题最多只能拿到它的最高选项分
            q_max = {}
            for opt in q["options"]:
                t = opt["target_type"]
                q_max[t] = max(q_max.get(t, 0), opt["score"])
            for t, val in q_max.items():
                max_scores[t] = max_scores.get(t, 0) + val
    return max_scores


MAX_SCORES = calculate_max_scores(QUESTIONS)

# 12 类人格的中文称号与评语

RESULT_MAP = {
    "R1": {"name": "Spark",
           "desc": "你是智医天选学委，你在主楼和图书馆留下的汗水足以灌溉整个医大和天大。字典里没有休息，只有对学术巅峰的极致追求。VOOC闪充是你的秘密武器，充电五分钟，学习两小时。嘘！不要告诉别人哦"},
    "R2": {"name": "6s' Cat",
           "desc": "你是一只六秒钟的猫。看到电路就会傻笑，听到万用表的报警声就会伤心，闻着焊锡味就能精神百倍。你的双手是代码与硬件的桥梁，STM32是你最亲密的战友，你在医疗仪器的制造上已经赶英超美，单枪匹马地闯出了自己的一片天。"},
    "R3": {"name": "TMU",
           "desc": "你是全国唯一一所医学院校中的211。牛蛙见你都要绕道走。深谙生物医学底层机理，手术刀在你手里比筷子还稳。智能医学工程里常说的懂代码懂仪器的医生就是你！"},
    "R4": {"name": "听见你说~",
           "desc": "在智能医学工程里，你会创造新的历史，你是一颗突然的陀螺，刚被工科类课程抽完左脸，马上又被医学课抽肿右脸。天天口号多，年年最幽默，你在旋转中领悟劳逸结合的真谛，能在智医活下去就是最大的胜利。"},
    "R5": {"name": "医路赞鸽",
           "desc": "你是一只美丽的医路赞鸽。哪有新店去哪吃，哪有八卦哪有你。比起冷冰冰的仪器，你更欣赏自己精致的OOTD，向往商业区繁华绚烂的夜景而非学校里零星的邈远灯光，你是智能医学工程天生的网红与明星。"},
    "R6": {"name": "风吹屁屁凉",
           "desc": "你是智能医学工程的蒙娜丽莎。你会思考为什么乌鸦像写字台，你是赫尔辛基的风琴，你是喜马拉雅山的长尾叶猴，你满嘴抽象名言，是玄学、代码与疯狂的最完美结合体。晴天、阴天、下雨天，你喜欢哪一天？"},
    "R7": {"name": "SSVEP",
           "desc": "你是一种特殊的事件相关电位，对同安道和气象台道小店的周期性视觉刺激产生的持续、同步的振荡响应。科研可以先等等，但绝不能错过一种美食。嘿嘿嘿嘿，要我~吃~掉你吗？嘻嘻嘻"},
    "R8": {"name": "鲶鱼王",
           "desc": "你是领地意识非常强烈的宝可梦。会把base全部当做自己的领地。如果有敌人接近，就会狂暴起来并创建一个docker锁住它。只要能conda activate，你就能创造奇迹。沉迷深度学习与脑机算法，通过Fine-tuning调节你和智能医学工程的关系。"},
    "R9": {"name": "神工-神甲",
           "desc": "你是一台专门为智医破防人设计的康复机器人，永远在担心期末考。前额叶工作记忆虽只有7秒，但你依然像一艘摇摇欲坠的老年皮划艇，在智能医学工程的惊涛骇浪里像区一样蠕动。"},
    "R10": {"name": "OXYGEN",
            "desc": "追求自由，不羁放纵。对于智能医学工程来说，你就是像氧气一般的人。它所有的条条框框都无法约束你，虽然在你面前它作为交叉学科几度颜面扫地，但是如果没有你，就无法衬托出智能医学工程其他同学的辛苦。IME是你的追求者，它在等待着你回头宠幸它的那一天"},
    "R11": {"name": "脑电帽",
            "desc": "你是智能医学工程生理活动的记录者。你是材料、硬件、软件、生物机理的集大成者，你是未来的顶层架构师。你的进步将会不断推动着神经科学、临床医学和人机交互领域的发展。"},
    "R12": {"name": "T1加权像",
            "desc": "T1加权像是磁共振成像的基石序列，你也是IME的基石人物。被专业课折磨千万次，依然待它如初恋。你能潜心研究课程内质子与周围晶格（组织大分子）之间的能量交换效率。你满怀希望，坚信IME能改变世界。"}
}


# ================= 3. 海报生成函数 =================
# def draw_justified_text(draw, x, y, text, font, fill, max_width, line_spacing):
#     """文本自动换行与两端对齐"""
#     if not text: return  # 如果没填文案，就不画了
#     lines = []
#     line = ""
#     for char in text:
#         test_line = line + char
#         w = font.getbbox(test_line)[2]
#         if w <= max_width:
#             line = test_line
#         else:
#             lines.append(line)
#             line = char
#     if line: lines.append(line)
#
#     current_y = y
#     for i, line in enumerate(lines):
#         if i == len(lines) - 1 or len(line) == 1:
#             draw.text((x, current_y), line, font=font, fill=fill)
#         else:
#             w = font.getbbox(line)[2]
#             extra_space = max_width - w
#             space_per_gap = extra_space / (len(line) - 1)
#             current_x = x
#             for char in line:
#                 draw.text((current_x, current_y), char, font=font, fill=fill)
#                 current_x += font.getbbox(char)[2] + space_per_gap
#         current_y += font.getbbox("测")[3] + line_spacing
#
#
# def generate_poster(r_code):
#     data = RESULT_MAP.get(r_code, {"name": "神秘人", "desc": ""})
#     type_name = data["name"]
#     desc_text = data["desc"]
#
#     bg = Image.new('RGB', (800, 1200), color='#F7F8FA')
#     draw = ImageDraw.Draw(bg)
#
#     font_path = "msyhbd.ttc"
#     if not os.path.exists(font_path): font_path = "msyhbd.ttc"
#
#     try:
#         title_font = ImageFont.truetype(font_path, 80)
#         desc_font = ImageFont.truetype(font_path, 28)
#     except:
#         st.error("字体文件缺失！");
#         return None
#
#     draw.text((400, 120), type_name, font=title_font, fill="#2E8B57", anchor="mm", stroke_width=2,
#               stroke_fill="#2E8B57")
#
#     img_path = f"images/{type_name}.png"
#     if not os.path.exists(img_path): img_path = f"images/{type_name}.jpg"
#
#     if os.path.exists(img_path):
#         img = Image.open(img_path).convert("RGBA").resize((600, 600))
#         bg.paste(img, (100, 250), img)
#     else:
#         draw.rectangle([100, 250, 700, 850], outline="#CCCCCC", width=5)
#         draw.text((400, 550), f"(请存入 {type_name}.png 或 .jpg)", font=desc_font, fill="#999999", anchor="mm")
#
#     draw_justified_text(draw, 100, 900, desc_text, desc_font, fill="#666666", max_width=600, line_spacing=18)
#     return bg
def draw_justified_text(draw, x, y, text, font, fill, max_width, line_spacing):
    """
    自定义函数：实现文本的像素级两端对齐
    """
    if not text: return
    lines = []
    line = ""
    # 1. 自动换行逻辑
    for char in text:
        test_line = line + char
        # 获取当前行像素宽度
        w = font.getbbox(test_line)[2]
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = char
    if line: lines.append(line)

    # 2. 绘制每一行
    current_y = y
    for i, line in enumerate(lines):
        # 最后一行或单字行不拉伸，直接左对齐
        if i == len(lines) - 1 or len(line) == 1:
            draw.text((x, current_y), line, font=font, fill=fill)
        else:
            # 计算需要分配的空白像素
            w = font.getbbox(line)[2]
            extra_space = max_width - w
            space_per_gap = extra_space / (len(line) - 1)

            current_x = x
            for char in line:
                draw.text((current_x, current_y), char, font=font, fill=fill)
                current_x += font.getbbox(char)[2] + space_per_gap

        # 换行：计算字符高度并叠加行间距
        current_y += font.getbbox("测")[3] + line_spacing


def generate_poster(r_code):
    data = RESULT_MAP.get(r_code, {"name": "神秘人", "desc": ""})
    type_name = data["name"]
    desc_text = data["desc"]

    bg = Image.new('RGB', (800, 1200), color='#F7F8FA')
    draw = ImageDraw.Draw(bg)

    font_path = "msyhbd.ttc"
    if not os.path.exists(font_path): font_path = "msyhbd.ttc"

    try:
        title_font = ImageFont.truetype(font_path, 80)
        desc_font = ImageFont.truetype(font_path, 28)
    except:
        st.error("字体文件缺失！");
        return None

    draw.text((400, 120), type_name, font=title_font, fill="#2E8B57", anchor="mm")
    img_path = f"images/{type_name}.png"
    if not os.path.exists(img_path): img_path = f"images/{type_name}.jpg"

    if os.path.exists(img_path):
        img = Image.open(img_path).convert("RGBA")

        # 【新增关键步骤】：根据 EXIF 信息自动校正旋转方向
        # 这会确保 3900*2900 的图片按照它该有的样子（横向或纵向）进行后续处理
        img = ImageOps.exif_transpose(img)

        # 等比例缩放
        img.thumbnail((600, 600), Image.Resampling.LANCZOS)

        # 居中计算
        paste_x = 100 + (600 - img.width) // 2
        paste_y = 250 + (600 - img.height) // 2
        bg.paste(img, (paste_x, paste_y), img)
    else:
        draw.rectangle([100, 250, 700, 850], outline="#CCCCCC", width=5)
        draw.text((400, 550), f"(请存入 {type_name}.png 或 .jpg)", font=desc_font, fill="#999999", anchor="mm")

    draw_justified_text(draw, 100, 900, desc_text, desc_font, fill="#666666", max_width=600, line_spacing=18)
    return bg

# ================= 4. 逻辑控制 =================
if 'current_index' not in st.session_state:
    st.session_state.current_index, st.session_state.type_scores = 0, {}

if st.session_state.current_index < len(QUESTIONS):
    curr_q = QUESTIONS[st.session_state.current_index]
    st.caption(f"第 {st.session_state.current_index + 1} / {len(QUESTIONS)} 题")
    st.progress((st.session_state.current_index + 1) / len(QUESTIONS))
    st.subheader(curr_q['text'])

    choices = [opt['text'] for opt in curr_q['options']]
    if curr_q.get("type") == "multiple":
        user_choice = st.multiselect("（可多选）", choices, key=f"q_{curr_q['id']}")
    else:
        user_choice = st.radio("请选择：", choices, index=None, key=f"q_{curr_q['id']}")

    if st.button("下一题", use_container_width=True):
        if user_choice:
            choice_list = user_choice if isinstance(user_choice, list) else [user_choice]
            for c in choice_list:
                opt_data = next(o for o in curr_q['options'] if o['text'] == c)
                t = opt_data['target_type']
                st.session_state.type_scores[t] = st.session_state.type_scores.get(t, 0) + opt_data['score']
            st.session_state.current_index += 1
            st.rerun()
        else:
            st.warning("请先做出选择")
else:
    # 答题结束，执行归一化计分逻辑
    st.balloons()
    scores = st.session_state.type_scores

    if scores:
        # 1. 计算每个获得分数的人格的“百分比契合度”
        normalized_scores = {}
        for r_code, score in scores.items():
            # 获取该人格的理论最高分，如果找不到默认给 1 防止除以 0
            max_possible = MAX_SCORES.get(r_code, 1) + 2
            normalized_scores[r_code] = score / max_possible

        # 2. 找到最高的契合度比例
        max_percentage = max(normalized_scores.values())

        # 3. 找出所有达到最高契合度的人格（处理平局情况）
        top_candidates = [k for k, v in normalized_scores.items() if v == max_percentage]

        # 4. 稀有度优先的平局决胜逻辑：
        # 如果有多个最高分，优先选择 MAX_SCORES 最小的那个（即题目最少、最难触发的隐藏款）
        best_r = min(top_candidates, key=lambda x: MAX_SCORES.get(x, 999))

        best_r_name = RESULT_MAP[best_r]["name"]

        st.markdown("<h3 style='text-align: center; color: black;'>你的IMETI是</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color: #2E8B57; font-weight: 900;'>{best_r_name}</h1>",
                    unsafe_allow_html=True)
        st.markdown("---")

        poster = generate_poster(best_r)
        if poster:
            st.image(poster, use_container_width=True)
            st.markdown("<p style='text-align:center; color:#888;'>👇 长按保存海报分享朋友圈</p>",
                        unsafe_allow_html=True)

    st.markdown("---")
    if st.button("再测一次", use_container_width=True):
        st.session_state.current_index, st.session_state.type_scores = 0, {}
        st.rerun()