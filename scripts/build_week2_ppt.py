"""生成周分享 2 PPT。

策略：基于周分享1.pptx，用其中带 bg 装饰的 layouts（Title Slide / Title Only），
保留所有视觉素材（红色装饰、MORE VALUE 角标、freeform 几何元素），仅在干净画布上添加内容。

主线：第二周预研内容（LangChain Agent / LangGraph / Context Engineering 三大模块），
项目作每个模块的最后一页案例。
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Cm, Pt

WEEK1 = Path(r"C:\Users\Z\Desktop\周分享\周分享1.pptx")
import os as _os

_DEFAULT_OUT = Path(r"C:\Users\Z\Desktop\周分享\周分享2.pptx")
OUT = Path(_os.environ.get("PPT_OUT", str(_DEFAULT_OUT)))
SHOTS = Path(r"C:\Users\Z\Desktop\周分享\周分享2")

# 配色（招商基金风格）
PRIMARY = RGBColor(0xC0, 0x39, 0x2B)
ACCENT = RGBColor(0x1F, 0x49, 0x7D)
DARK = RGBColor(0x33, 0x33, 0x33)
GREY = RGBColor(0x66, 0x66, 0x66)
LIGHT_GREY = RGBColor(0xEE, 0xEE, 0xEE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# 内容区参考边界（cm，16:9 = 33.87 x 19.05）
SLIDE_W = 33.87
SLIDE_H = 19.05


# ============================================================
# Helpers
# ============================================================

def _delete_all_slides(prs: Presentation) -> None:
    sldIdLst = prs.slides._sldIdLst
    rid_attr = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    for sldId in list(sldIdLst):
        prs.part.drop_rel(sldId.attrib[rid_attr])
        sldIdLst.remove(sldId)


def _layout(prs: Presentation, name: str):
    for lo in prs.slide_layouts:
        if lo.name == name:
            return lo
    return prs.slide_layouts[1]


def _new_slide(prs: Presentation, layout_name: str, *, drop_placeholders: bool = True):
    """新建 slide，layout 自带的装饰 shapes 保留，placeholders 全部删掉留干净画布。"""
    s = prs.slides.add_slide(_layout(prs, layout_name))
    if drop_placeholders:
        for ph in list(s.placeholders):
            ph._element.getparent().remove(ph._element)
    return s


def _txt(slide, x_cm, y_cm, w_cm, h_cm, text, *,
         size=14, bold=False, color=DARK, align=PP_ALIGN.LEFT,
         vert=MSO_ANCHOR.TOP, font_name="微软雅黑"):
    tb = slide.shapes.add_textbox(Cm(x_cm), Cm(y_cm), Cm(w_cm), Cm(h_cm))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = vert
    tf.margin_left = Cm(0.05); tf.margin_right = Cm(0.05)
    tf.margin_top = Cm(0.05); tf.margin_bottom = Cm(0.05)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        r = para.add_run()
        r.text = line
        r.font.name = font_name
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return tb


def _bullets(slide, x, y, w, h, items, *, size=12, color=DARK, bullet=PRIMARY,
             space_after=4):
    tb = slide.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(space_after)
        bul = p.add_run()
        bul.text = "• "
        bul.font.name = "微软雅黑"; bul.font.size = Pt(size)
        bul.font.bold = True; bul.font.color.rgb = bullet
        run = p.add_run()
        run.text = item
        run.font.name = "微软雅黑"; run.font.size = Pt(size)
        run.font.color.rgb = color
    return tb


def _section_header(slide, num, title):
    """页面左上角大号 '01 标题' header。"""
    n = slide.shapes.add_textbox(Cm(0.8), Cm(0.5), Cm(2.5), Cm(1.6))
    tf = n.text_frame
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = num
    r.font.name = "Arial"; r.font.size = Pt(32); r.font.bold = True
    r.font.color.rgb = PRIMARY

    t = slide.shapes.add_textbox(Cm(3.2), Cm(0.85), Cm(28), Cm(1.2))
    tf = t.text_frame
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = title
    r.font.name = "微软雅黑"; r.font.size = Pt(22); r.font.bold = True
    r.font.color.rgb = DARK

    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(0.8), Cm(2.3), Cm(2), Cm(0.08))
    bar.fill.solid(); bar.fill.fore_color.rgb = PRIMARY
    bar.line.fill.background()


def _code_block(slide, x, y, w, h, code, *, size=10):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y), Cm(w), Cm(h))
    box.fill.solid(); box.fill.fore_color.rgb = RGBColor(0x2B, 0x2B, 0x2B)
    box.line.fill.background()
    tf = box.text_frame
    tf.margin_left = Cm(0.3); tf.margin_right = Cm(0.3)
    tf.margin_top = Cm(0.2); tf.margin_bottom = Cm(0.2)
    tf.word_wrap = True
    for i, line in enumerate(code.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = line if line else " "
        r.font.name = "Consolas"; r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0xE6, 0xE6, 0xE6)


def _pic(slide, path, x, y, w=None, h=None):
    if not path.exists():
        return None
    kw = {"left": Cm(x), "top": Cm(y)}
    if w: kw["width"] = Cm(w)
    if h: kw["height"] = Cm(h)
    return slide.shapes.add_picture(str(path), **kw)


def _table(slide, x, y, col_widths_cm, rows,
           header_fill=PRIMARY, alt_fill=LIGHT_GREY, base_fill=WHITE,
           header_color=WHITE, body_color=DARK, font_size=11, row_h=1.0):
    """简单表格：第一行表头。rows[i][j] 为单元格文本。"""
    cur_y = y
    for ri, row in enumerate(rows):
        cur_x = x
        for ci, cell in enumerate(row):
            cw = col_widths_cm[ci]
            rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(cur_x), Cm(cur_y),
                                          Cm(cw), Cm(row_h))
            if ri == 0:
                rect.fill.solid(); rect.fill.fore_color.rgb = header_fill
                rect.line.fill.background()
                tcolor = header_color; bold = True
            else:
                rect.fill.solid()
                rect.fill.fore_color.rgb = base_fill if ri % 2 else alt_fill
                rect.line.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
                tcolor = body_color
                bold = (ci == 0)
            tf = rect.text_frame
            tf.margin_left = Cm(0.2); tf.margin_right = Cm(0.2)
            tf.margin_top = Cm(0.15); tf.margin_bottom = Cm(0.15)
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run(); r.text = cell
            r.font.name = "微软雅黑"; r.font.size = Pt(font_size)
            r.font.bold = bold; r.font.color.rgb = tcolor
            cur_x += cw
        cur_y += row_h


def _footer_pageno(slide, num, total):
    tb = slide.shapes.add_textbox(Cm(SLIDE_W - 3), Cm(SLIDE_H - 1.0), Cm(2.5), Cm(0.5))
    tf = tb.text_frame
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    r = p.add_run(); r.text = f"{num} / {total}"
    r.font.name = "Arial"; r.font.size = Pt(9); r.font.color.rgb = GREY


# ============================================================
# Build
# ============================================================

def build():
    prs = Presentation(str(WEEK1))
    _delete_all_slides(prs)

    # 检测可用 layout 名（可能是中文或英文）
    layout_names = [lo.name for lo in prs.slide_layouts]
    print("available layouts:", layout_names)

    # 优先使用带 bg 装饰的 layouts
    cover_layout = "Title Slide" if "Title Slide" in layout_names else layout_names[0]
    content_layout = "Title Only" if "Title Only" in layout_names else "Title and Content"
    two_layout = "Two Content" if "Two Content" in layout_names else content_layout

    builders = []

    # ========== 1. 封面 ==========
    def slide_1():
        s = _new_slide(prs, cover_layout)
        _txt(s, 1.5, 6.5, 30, 2.2, "Agent 技术框架与产品实践分享 02",
             size=34, bold=True, color=DARK)
        _txt(s, 1.5, 9.2, 30, 1.5,
             "—— LangChain · LangGraph · Context Engineering",
             size=20, color=PRIMARY)
        _txt(s, 1.5, 11, 30, 1, "第二周预研分享", size=14, color=GREY)
        # 信息行
        _txt(s, 1.5, 16.5, 20, 0.8, "分享人：温舒麟", size=12, color=DARK)
        _txt(s, 1.5, 17.4, 20, 0.8, "部门：信息技术部 - 开发三组", size=12, color=DARK)
        return s
    builders.append(slide_1)

    # ========== 2. 目录（三大模块）==========
    def slide_2():
        s = _new_slide(prs, content_layout)
        _section_header(s, "", "本周分享 · 三大模块")
        items = [
            ("01", "LangChain Agent 架构",
             "Agent 编排演进 · create_agent · Middleware 横切机制"),
            ("02", "LangGraph 图编排",
             "Graph Runtime · State / Reducer · Send 并行 · Subgraph"),
            ("03", "Context Engineering & LangSmith",
             "上下文工程 · Tracing · Evals · Studio · Platform"),
        ]
        top = 4.5
        for num, title, sub in items:
            _txt(s, 1.5, top, 2.5, 1.8, num, size=44, bold=True, color=PRIMARY)
            _txt(s, 5, top + 0.4, 27, 1.2, title, size=20, bold=True, color=DARK)
            _txt(s, 5, top + 1.6, 27, 1, sub, size=13, color=GREY)
            top += 4.0
        return s
    builders.append(slide_2)

    # ============================================================
    # 模块 01：LangChain Agent 架构（4 页）
    # ============================================================

    # 3. 01-1 Agent 编排概览
    def slide_3():
        s = _new_slide(prs, content_layout)
        _section_header(s, "01", "Agent 编排概览：从 Chain 到 Graph")
        _txt(s, 1.5, 3, 31, 0.8, "LangChain 1.0 把单 Agent 与多步流程明确分到两个产品",
             size=14, color=GREY)
        _table(s, 1.5, 4.2, [4.5, 12.5, 12.5], [
            ["",            "LangChain Agent（create_agent）", "LangGraph"],
            ["定位",         "单 Agent 标准模式：模型 + 工具循环", "复杂工作流：多节点、分支、循环、并行"],
            ["典型场景",     "ReAct、客服 chatbot、tool-using agent", "审批流、质检、研究流水线、人机协同"],
            ["控制粒度",     "中等：middleware 钩子",                "高：每条边 / 每个节点都能定制"],
            ["状态",         "消息历史为主",                          "TypedDict + 自定义 reducer"],
            ["可观测",       "LangSmith 自动追踪",                    "LangSmith + Studio 可视化调试"],
        ], row_h=1.3)
        _txt(s, 1.5, 14, 31, 1,
             "👉 单 Agent 解决一类任务，多步流程要靠 Graph 编排；中间用 Middleware 拼接共性能力",
             size=13, bold=True, color=ACCENT)
        return s
    builders.append(slide_3)

    # 4. 01-2 create_agent
    def slide_4():
        s = _new_slide(prs, content_layout)
        _section_header(s, "01", "create_agent：标准 ReAct 模式")
        _txt(s, 1.5, 3, 31, 0.7,
             "LangChain 1.0 内置的单 Agent 工厂，一行代码起一个会用工具的 Agent",
             size=13, color=GREY)
        _code_block(s, 1.5, 4.2, 18, 9, """from langchain.agents import create_agent
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    \"\"\"查询城市天气\"\"\"
    return f"{city}: 23°C"

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[get_weather],
    system_prompt="你是天气助手",
)

response = agent.invoke({"messages": "今天上海天气？"})""", size=11)

        _txt(s, 20.5, 4.2, 12, 0.6, "运行机制（ReAct Loop）",
             size=13, bold=True, color=PRIMARY)
        _bullets(s, 20.5, 5.1, 12, 7, [
            "用户输入 → 模型判断要不要调工具",
            "要 → 生成 tool call → 执行 → 结果回填",
            "不要 → 直接回答",
            "循环直到模型说\"完成\"",
        ], size=12)

        _txt(s, 20.5, 9.8, 12, 0.6, "局限",
             size=13, bold=True, color=PRIMARY)
        _bullets(s, 20.5, 10.6, 12, 5, [
            "只有一个 Agent + 一个工具循环",
            "想加分支 / 循环 / 并行 → 力不从心",
            "复杂业务流程要拆出多 Agent",
            "→ 用 LangGraph 显式编排",
        ], size=12)
        return s
    builders.append(slide_4)

    # 5. 01-3 Middleware
    def slide_5():
        s = _new_slide(prs, content_layout)
        _section_header(s, "01", "Middleware：横切关注点的标准机制")
        _txt(s, 1.5, 3, 31, 0.8,
             "在 LLM 调用前后插入逻辑，业务节点零侵入",
             size=14, color=GREY)
        # 三个 hook 卡片
        cards = [
            ("before_model", "调模型前", PRIMARY,
             "注入上下文\nPII 脱敏\n权限检查\n动态 system prompt"),
            ("after_model", "调模型后", ACCENT,
             "日志 / 审计\n成本统计\n输出审查\n格式校验"),
            ("wrap_model_call", "完全包装", RGBColor(0x2E, 0x7D, 0x32),
             "重试 / 降级\n响应缓存\n模型故障切换\n限流"),
        ]
        x0 = 1.5; y0 = 4.3; cw = 10.2; ch = 8; gap = 0.5
        for i, (name, when, color, content) in enumerate(cards):
            x = x0 + i * (cw + gap)
            top = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y0), Cm(cw), Cm(0.7))
            top.fill.solid(); top.fill.fore_color.rgb = color; top.line.fill.background()
            body = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y0 + 0.7), Cm(cw), Cm(ch - 0.7))
            body.fill.solid(); body.fill.fore_color.rgb = WHITE
            body.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
            _txt(s, x + 0.3, y0 + 0.05, cw - 0.6, 0.7, name,
                 size=13, bold=True, color=WHITE, font_name="Consolas")
            _txt(s, x + 0.4, y0 + 1, cw - 0.8, 0.8, when,
                 size=12, bold=True, color=DARK)
            _txt(s, x + 0.4, y0 + 2.1, cw - 0.8, 5, content,
                 size=12, color=DARK)

        _txt(s, 1.5, 13.2, 31, 0.7, "为什么把这些抽出来？",
             size=14, bold=True, color=DARK)
        _bullets(s, 1.5, 14, 31, 4, [
            "PII 脱敏 / 成本统计 / 审计这些功能跟具体业务无关，每个节点都需要 → 中间件",
            "改实现不动业务代码：换脱敏算法、加新模型，只改 middleware",
            "可叠加：多个 middleware 像洋葱一样层层包装",
        ], size=12)
        return s
    builders.append(slide_5)

    # 6. 01-4 项目案例：Middleware
    def slide_6():
        s = _new_slide(prs, content_layout)
        _section_header(s, "01", "项目案例：PII 脱敏 + 成本追踪")
        _txt(s, 1.5, 3, 31, 0.7,
             "用一个金融通话质检系统印证 Middleware 的价值",
             size=13, color=GREY)
        _code_block(s, 1.5, 4, 17, 4.5, """# middleware/pii.py — 一次性脱敏
def redact_pii(text):
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text

# input_node.py 唯一调用点
def input_node(state):
    return {"conversation": redact_pii(state["conversation"])}""", size=10)
        _code_block(s, 1.5, 9, 17, 4, """# llm.py — 包装 LLM 调用，捕获 token 用量
def invoke_structured(schema, messages, *, node_name):
    model = get_chat_model()
    bound = model.with_structured_output(schema, include_raw=True)
    result = bound.invoke(messages)
    usage = result["raw"].usage_metadata
    return result["parsed"], _record(node_name, usage)""", size=10)

        _pic(s, SHOTS / "成本计算.png", 19.5, 4, w=13)
        _txt(s, 19.5, 13.5, 13, 0.7, "实测",
             size=13, bold=True, color=PRIMARY)
        _bullets(s, 19.5, 14.3, 13, 3, [
            "一通 12s 通话 = $0.0024",
            "rule_scorer 占 67% 成本",
            "question_extractor 隐藏调用 2 次（结构化输出 retry）",
        ], size=11)
        return s
    builders.append(slide_6)

    # ============================================================
    # 模块 02：LangGraph Graph Runtime（6 页）
    # ============================================================

    # 7. 02-1 为什么需要图编排
    def slide_7():
        s = _new_slide(prs, content_layout)
        _section_header(s, "02", "为什么需要图编排？")
        _txt(s, 1.5, 3, 31, 0.8,
             "线性 Chain 与单 Agent 都解决不了的三类问题",
             size=14, color=GREY)
        cases = [
            ("分支", "根据中间结果选择不同后续路径",
             "命中合规风险 → 直接判 0\n非致命 → 继续累加扣分"),
            ("循环", "重复执行直到满足条件",
             "打分 → 审核\n审核不通过 → 回去重打分\n最多 3 次"),
            ("并行", "多任务同时跑、最后合并",
             "30 条规则各自评分\n并行执行 → 结果汇总\n延迟从 O(n) 降到常数"),
        ]
        x0 = 1.5; y0 = 4.3; cw = 10.2; ch = 8.5; gap = 0.5
        for i, (head, sub, ex) in enumerate(cases):
            x = x0 + i * (cw + gap)
            top = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y0), Cm(cw), Cm(0.8))
            top.fill.solid(); top.fill.fore_color.rgb = PRIMARY; top.line.fill.background()
            body = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y0 + 0.8), Cm(cw), Cm(ch - 0.8))
            body.fill.solid(); body.fill.fore_color.rgb = WHITE
            body.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
            _txt(s, x + 0.3, y0 + 0.1, cw - 0.6, 0.7, head,
                 size=15, bold=True, color=WHITE)
            _txt(s, x + 0.4, y0 + 1.1, cw - 0.8, 1.5, sub,
                 size=13, color=DARK)
            _txt(s, x + 0.4, y0 + 3.5, cw - 0.8, 5, ex,
                 size=12, color=GREY)

        _txt(s, 1.5, 13.5, 31, 1,
             "👉 LangGraph 把流程画成有向图，框架管 state、调度、并发、循环",
             size=13, bold=True, color=ACCENT)
        return s
    builders.append(slide_7)

    # 8. 02-2 核心组件 Node / Edge / State
    def slide_8():
        s = _new_slide(prs, content_layout)
        _section_header(s, "02", "核心组件：Node / Edge / State")
        cards = [
            ("Node 节点", "纯函数：state → 状态增量",
             "可纯计算，也可调 LLM / 工具\n返回 dict 表示要更新的字段", PRIMARY),
            ("Edge 边", "节点间的连接关系",
             "固定边：A → B\n条件边：函数返回下一个节点名\nSend：动态 fan-out 到多个实例", ACCENT),
            ("State 状态", "TypedDict + Reducer",
             "跨节点共享，自动合并\nReducer 决定多个写入怎么聚合\n（覆盖 / 累加 / 自定义）", RGBColor(0x2E, 0x7D, 0x32)),
        ]
        x0 = 1.5; y0 = 3.5; cw = 10.2; ch = 6.5; gap = 0.5
        for i, (head, lead, body, color) in enumerate(cards):
            x = x0 + i * (cw + gap)
            top = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y0), Cm(cw), Cm(0.7))
            top.fill.solid(); top.fill.fore_color.rgb = color; top.line.fill.background()
            box = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y0 + 0.7), Cm(cw), Cm(ch - 0.7))
            box.fill.solid(); box.fill.fore_color.rgb = WHITE
            box.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
            _txt(s, x + 0.3, y0 + 0.05, cw - 0.6, 0.7, head,
                 size=14, bold=True, color=WHITE)
            _txt(s, x + 0.4, y0 + 1, cw - 0.8, 1.2, lead,
                 size=12, bold=True, color=color)
            _txt(s, x + 0.4, y0 + 2.4, cw - 0.8, 4, body,
                 size=11, color=DARK)

        _txt(s, 1.5, 10.7, 31, 0.6, "最小可运行例子",
             size=13, bold=True, color=DARK)
        _code_block(s, 1.5, 11.5, 31, 6, """class State(TypedDict):
    messages: list[str]

def greet(state):
    return {"messages": state["messages"] + ["hello"]}

g = StateGraph(State)
g.add_node("greet", greet)
g.add_edge(START, "greet"); g.add_edge("greet", END)
graph = g.compile()
graph.invoke({"messages": []})    # → {"messages": ["hello"]}""", size=10)
        return s
    builders.append(slide_8)

    # 9. 02-3 Reducer
    def slide_9():
        s = _new_slide(prs, content_layout)
        _section_header(s, "02", "State Reducer：并行写入的合并机制")
        _txt(s, 1.5, 3, 31, 0.8,
             "默认：多个节点写同一字段 → 后写覆盖前写（数据丢失）。"
             "Reducer 解决这个问题。",
             size=13, color=GREY)
        _txt(s, 1.5, 4.5, 15, 0.6, "默认行为（覆盖）", size=13, bold=True, color=GREY)
        _code_block(s, 1.5, 5.3, 15, 4, """class State(TypedDict):
    deductions: list[dict]

# 5 个并行 scorer 各自写 deductions
# → 只有最后一个写入留下，前 4 个被覆盖""", size=11)

        _txt(s, 17, 4.5, 15, 0.6, "用 Annotated[..., reducer]", size=13, bold=True, color=PRIMARY)
        _code_block(s, 17, 5.3, 15, 4, """class State(TypedDict):
    deductions: Annotated[
        list[dict],
        list_add_or_reset,    # 自定义合并
    ]

def list_add_or_reset(left, right):
    if right is RESET:
        return []                           # 重置
    return (left or []) + (right or [])    # 累加""", size=10)

        _txt(s, 1.5, 10.2, 31, 0.6, "在循环中怎么用",
             size=13, bold=True, color=ACCENT)
        _bullets(s, 1.5, 11, 31, 6, [
            "scoring_dispatcher 进入新一轮时返回 {\"deductions\": RESET} → 清空",
            "5 个并行 rule_scorer 各自 append → reducer 自动累加",
            "auditor 看到完整列表，做整体判断",
            "审核不通过 → 回到 dispatcher → 再次 RESET 开始下一轮",
        ], size=12)

        _txt(s, 1.5, 16.2, 31, 1,
             "👉 LangGraph 内置 add_messages（消息列表自动追加）；其余字段用自定义 reducer",
             size=12, bold=True, color=ACCENT)
        return s
    builders.append(slide_9)

    # 10. 02-4 Send
    def slide_10():
        s = _new_slide(prs, content_layout)
        _section_header(s, "02", "Send：动态 fan-out / map-reduce 编排")
        _txt(s, 1.5, 3, 31, 0.8,
             "条件边返回 [Send(node, payload), ...] → 启动 N 个并行实例",
             size=13, color=GREY)
        _code_block(s, 1.5, 4.2, 17, 7, """from langgraph.types import Send

def fan_out(state):
    return [
        Send("rule_scorer", {
            "rule": rule,
            "conversation": state["conversation"],
        })
        for rule in state["rules_json"]
    ]

g.add_conditional_edges("dispatcher", fan_out, ["rule_scorer"])
# 5 条规则 → 5 个 rule_scorer 并行
# 各自返回的 deductions 通过 reducer 合并""", size=11)

        _txt(s, 19.5, 4.2, 13, 0.6, "执行模型",
             size=13, bold=True, color=PRIMARY)
        _bullets(s, 19.5, 5, 13, 6, [
            "BFS 推进：当前层完成 → 下一层",
            "Send 在条件边里返回 → 派多个实例",
            "每个 Send 携带专属 payload",
            "实例可以是同名节点的多个并行执行",
            "下游边自动等待所有 Send 完成（fan-in）",
        ], size=12)

        _txt(s, 19.5, 11, 13, 0.6, "经典用例",
             size=13, bold=True, color=ACCENT)
        _bullets(s, 19.5, 11.8, 13, 4, [
            "map-reduce：每条数据一个 worker",
            "并行规则评估",
            "多查询并发检索",
        ], size=12)
        return s
    builders.append(slide_10)

    # 11. 02-5 Subgraph
    def slide_11():
        s = _new_slide(prs, content_layout)
        _section_header(s, "02", "Subgraph：模块化封装")
        _txt(s, 1.5, 3, 31, 0.8,
             "把一组节点编译成单元，作为父图的一个 \"节点\" 使用",
             size=13, color=GREY)
        _code_block(s, 1.5, 4.2, 18, 7, """def build_scoring_subgraph():
    g = StateGraph(GraphState)
    g.add_node("scoring_dispatcher", ...)
    g.add_node("rule_scorer", rule_scorer)
    g.add_node("auditor", auditor)
    # 内部循环
    g.add_conditional_edges("auditor", route_audit, ...)
    return g.compile()

# 主图把子图当作普通节点
parent.add_node("scoring_with_audit", build_scoring_subgraph())""", size=11)

        _txt(s, 20.5, 4.2, 12, 0.6, "为什么要抽 Subgraph",
             size=13, bold=True, color=PRIMARY)
        _bullets(s, 20.5, 5, 12, 8, [
            "主图保持简洁：从外面看就是一条流水线",
            "可独立测试：单独 compile + 单测",
            "可复用：同一个 \"draft + critique\" 模式用在多处",
            "Studio 可视化：双击展开内部",
            "状态自动透传：父子图共享同名 state 键",
        ], size=11)

        _txt(s, 1.5, 12.5, 31, 0.6, "状态合并规则",
             size=13, bold=True, color=ACCENT)
        _bullets(s, 1.5, 13.3, 31, 3, [
            "父子图共用 GraphState：同名 TypedDict 键自动对齐，不需要任何 plumbing",
            "子图返回的状态增量按父图的 reducer 合并到父状态",
            "子图内部状态不污染父图，封装边界清晰",
        ], size=12)
        return s
    builders.append(slide_11)

    # 12. 02-6 项目案例：架构演进
    def slide_12():
        s = _new_slide(prs, content_layout)
        _section_header(s, "02", "项目案例：通话质检系统架构演进")
        _txt(s, 1.5, 3, 15, 0.7, "v1：6 节点线性 + 反馈边", size=13, bold=True, color=GREY)
        _pic(s, SHOTS / "初始图.png", 1.5, 3.8, w=15)
        _txt(s, 17, 3, 15, 0.7, "v2：5 节点 + 子图 + 并行", size=13, bold=True, color=PRIMARY)
        _pic(s, SHOTS / "节点图.png", 17, 3.8, w=15)

        _txt(s, 1.5, 14.3, 31, 0.7, "演进路径",
             size=13, bold=True, color=DARK)
        _bullets(s, 1.5, 15.1, 31, 4, [
            "scoring_loop ⇄ auditor 抽成 subgraph → 主图变 5 节点流水线",
            "subgraph 内 scoring_loop 拆成 dispatcher + 多 rule_scorer + extraction → Send 并行",
            "5 规则评分延迟：~10s → 12.5s（含 fan-out 开销，30 规则估算 13-15s）",
        ], size=12)
        return s
    builders.append(slide_12)

    # ============================================================
    # 模块 03：Context Engineering & LangSmith（5 页）
    # ============================================================

    # 13. 03-1 Prompt → Context Engineering
    def slide_13():
        s = _new_slide(prs, content_layout)
        _section_header(s, "03", "从 Prompt Engineering 到 Context Engineering")
        _txt(s, 1.5, 3, 31, 0.8,
             "重点不再是 \"把一句话写好\"，而是 \"动态拼出最适合当前任务的上下文\"",
             size=13, color=GREY)
        _table(s, 1.5, 4.2, [10, 11, 11], [
            ["", "Prompt Engineering", "Context Engineering"],
            ["关注点",   "单条 prompt 怎么写",       "上下文系统怎么设计"],
            ["手段",     "措辞 / few-shot / 角色扮演", "检索 / 摘要 / 工具描述 / schema 注入"],
            ["可改性",   "改 prompt 字符串",          "改架构（节点 / state / 检索器）"],
            ["产出",     "一条好的 prompt",           "一个能持续供给好上下文的系统"],
        ], row_h=1.4)
        _txt(s, 1.5, 13.5, 31, 1.2,
             "👉 Andrej Karpathy：\"软件 3.0 不是写代码，是工程化地构造模型上下文\"",
             size=13, bold=True, color=ACCENT)
        return s
    builders.append(slide_13)

    # 14. 03-2 上下文设计的几个层次
    def slide_14():
        s = _new_slide(prs, content_layout)
        _section_header(s, "03", "上下文设计的几个层次")
        layers = [
            ("结构化输出", "with_structured_output(Schema)", PRIMARY,
             "用 Pydantic schema 约束 LLM 返回\n避免 \"模型偷懒返回空数组\"\n本周项目实测：hot_words 从 [] → 5 个高价值词"),
            ("知识检索", "RAG / KB lookup", ACCENT,
             "从向量库 / 关键词库取参考答案\n注入进 prompt 给模型比对\n本周项目：客户问题 → KB 查 → 答非所问扣 rule 17"),
            ("Few-shot 示例", "动态注入历史好/坏例子", RGBColor(0x2E, 0x7D, 0x32),
             "对 LLM 来说，\"看过几个对的就更会了\"\n可从过去 trace / golden set 里采样\n下周可加：从 Evals 失败例子注入反例"),
            ("反馈循环", "审核结果回馈给打分", RGBColor(0xEF, 0x6C, 0x00),
             "上一轮的 audit_issues → 当前轮的 input\n让模型 \"知道自己上次哪儿错了\"\n本周项目：scoring 重试时收到 issues"),
        ]
        x0 = 1.5; y0 = 3.5; cw = 30; rh = 2.7
        for i, (head, code, color, body) in enumerate(layers):
            y = y0 + i * (rh + 0.15)
            bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x0), Cm(y), Cm(0.4), Cm(rh))
            bar.fill.solid(); bar.fill.fore_color.rgb = color; bar.line.fill.background()
            _txt(s, x0 + 0.7, y + 0.1, 12, 0.8, head, size=14, bold=True, color=color)
            _txt(s, x0 + 0.7, y + 0.95, 12, 0.6, code,
                 size=11, color=GREY, font_name="Consolas")
            _txt(s, x0 + 13, y + 0.1, cw - 13, rh, body, size=11, color=DARK)
        return s
    builders.append(slide_14)

    # 15. 03-3 LangSmith Tracing
    def slide_15():
        s = _new_slide(prs, content_layout)
        _section_header(s, "03", "LangSmith Tracing：可观测性的基础")
        _txt(s, 1.5, 3, 31, 0.7,
             ".env 设 4 个变量，LangChain 自动上传每次调用，零代码",
             size=13, color=GREY)
        _pic(s, SHOTS / "追踪.png", 1.5, 3.9, w=22)
        _txt(s, 24.5, 4, 8.5, 0.7, "Trace 视图能看到", size=13, bold=True, color=PRIMARY)
        _bullets(s, 24.5, 4.9, 8.5, 8, [
            "完整调用树：每个节点 / LLM",
            "Waterfall 时间线",
            "input / output / token 用量",
            "失败 trace 标红可重放",
            "支持搜索 / 过滤 / 分组",
        ], size=11)
        _txt(s, 24.5, 12, 8.5, 0.7, "用法", size=13, bold=True, color=ACCENT)
        _bullets(s, 24.5, 12.8, 8.5, 4, [
            "LANGCHAIN_TRACING_V2=true",
            "LANGCHAIN_API_KEY=lsv2_...",
            "LANGCHAIN_PROJECT=name",
        ], size=10)
        return s
    builders.append(slide_15)

    # 16. 03-4 Evals
    def slide_16():
        s = _new_slide(prs, content_layout)
        _section_header(s, "03", "LangSmith Evals：从 \"感觉变好\" 到指标")
        _txt(s, 1.5, 3, 31, 0.7,
             "黄金数据集 + 评估器 + 实验对比 = 改 prompt 的回归保险",
             size=13, color=GREY)
        _pic(s, SHOTS / "黄金数据库和实验.png", 1.5, 4, w=15)
        _pic(s, SHOTS / "柱状图.png", 17, 4, w=15)

        _txt(s, 1.5, 12.5, 15, 0.7, "黄金数据集（4 个例子）",
             size=12, bold=True, color=PRIMARY)
        _bullets(s, 1.5, 13.2, 15, 4, [
            "clean_compliant：合规通话",
            "missing_greeting：缺话术",
            "fatal_guarantee：致命违规",
            "kb_mismatch：答非所问",
        ], size=11)

        _txt(s, 17, 12.5, 15, 0.7, "4 个评估器（baseline 实测）",
             size=12, bold=True, color=ACCENT)
        _bullets(s, 17, 13.2, 15, 4, [
            "rule_match: 75%（Jaccard 命中）",
            "fatal_correctness: 75%（精确）",
            "score_in_range: 100%",
            "review_match: 100%",
        ], size=11)
        return s
    builders.append(slide_16)

    # 17. 03-5 Studio + Platform
    def slide_17():
        s = _new_slide(prs, content_layout)
        _section_header(s, "03", "Studio 调试 + Platform 一键部署")
        _txt(s, 1.5, 3, 15, 0.7, "Studio（langgraph dev）",
             size=13, bold=True, color=PRIMARY)
        _pic(s, SHOTS / "节点图.png", 1.5, 3.8, w=15)
        _txt(s, 17, 3, 15, 0.7, "Platform 部署",
             size=13, bold=True, color=ACCENT)
        _pic(s, SHOTS / "部署.png", 17, 3.8, w=15)
        _txt(s, 1.5, 14.3, 31, 0.7, "工作流", size=13, bold=True, color=DARK)
        _bullets(s, 1.5, 15.1, 31, 4, [
            "本地 langgraph dev → 浏览器打开 Studio，节点图实时展开 / 重放 / 单步",
            "推到 GitHub → LangSmith Platform 一键部署成 HTTPS API + 持久 thread",
            "环境变量在 Platform UI 配置（DEEPSEEK_API_KEY 等）",
        ], size=12)
        return s
    builders.append(slide_17)

    # ============================================================
    # 18. 总结
    # ============================================================

    def slide_18():
        s = _new_slide(prs, content_layout)
        _section_header(s, "结", "总结与下周方向")
        _txt(s, 1.5, 3, 15, 0.8, "本周关键认知", size=15, bold=True, color=PRIMARY)
        _bullets(s, 1.5, 4.2, 15, 9, [
            "create_agent 解决单 Agent 标准模式",
            "复杂流程要靠 LangGraph 显式编排",
            "Send + Reducer + Subgraph 是并行编排三件套",
            "Middleware 抽走横切关注点（合规 / 成本）",
            "Context Engineering ＞ Prompt Engineering",
            "LangSmith 三件套补齐工程化（Trace / Evals / Platform）",
            "概念都已在质检项目验证过",
        ], size=12)

        _txt(s, 17.5, 3, 15, 0.8, "下周预告：第 3 周", size=15, bold=True, color=ACCENT)
        _bullets(s, 17.5, 4.2, 15, 7, [
            "Skills 模块化与 anthropics/skills 仓库",
            "MCP（Model Context Protocol）协议",
            "Tools 规模化：质检 KB → MCP server",
            "Claude Agent SDK 与 Subagent 调度",
            "可选实验：把本地 KB 升级成向量库",
        ], size=12)

        _txt(s, 1.5, 14.5, 31, 1, "项目仓库",
             size=13, bold=True, color=DARK)
        _txt(s, 1.5, 15.4, 31, 0.8,
             "github.com/wensl121/ai-call-quality",
             size=13, color=ACCENT, font_name="Consolas")
        _txt(s, 1.5, 16.4, 31, 0.7,
             "11 个 commit · 11 测试全过 · LangSmith Platform 部署可用",
             size=11, color=GREY)
        return s
    builders.append(slide_18)

    # 生成所有
    total = len(builders)
    for i, fn in enumerate(builders):
        slide = fn()
        if i > 0:
            _footer_pageno(slide, i + 1, total)

    prs.save(str(OUT))
    print(f"[done] {OUT}  ({total} slides)")


if __name__ == "__main__":
    build()
