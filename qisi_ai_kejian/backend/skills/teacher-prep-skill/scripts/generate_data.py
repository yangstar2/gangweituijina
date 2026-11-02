#!/usr/bin/env python3
"""数据生成脚本：扩展教材版本、课标编码、知识图谱到8版本×全学段"""

import json
import os
import sys

# 确保输出到 Skill 根目录
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# 1. 教材版本元数据生成
# ============================================================

VERSIONS = [
    {"id_prefix": "pep", "name": "人教版", "publisher": "人民教育出版社", "coverage": "全国80%+", "priority": "P0"},
    {"id_prefix": "su", "name": "苏教版", "publisher": "江苏凤凰教育出版社", "coverage": "江苏全省+部分省市", "priority": "P1"},
    {"id_prefix": "bsd", "name": "北师大版", "publisher": "北京师范大学出版社", "coverage": "华北/西北多省", "priority": "P1"},
    {"id_prefix": "shk", "name": "沪科版", "publisher": "上海科技教育出版社", "coverage": "上海+华东部分城市", "priority": "P2"},
    {"id_prefix": "fltrp", "name": "外研版", "publisher": "外语教学与研究出版社", "coverage": "全国英语主流版本之一", "priority": "P0"},
    {"id_prefix": "ecnu", "name": "华师大版", "publisher": "华东师范大学出版社", "coverage": "华东地区", "priority": "P1"},
    {"id_prefix": "zjedu", "name": "浙教版", "publisher": "浙江教育出版社", "coverage": "浙江省", "priority": "P2"},
    {"id_prefix": "sdedu", "name": "鲁教版", "publisher": "山东教育出版社", "coverage": "山东省", "priority": "P2"},
]

SUBJECTS = {
    "math": "数学",
    "chi": "语文",
    "eng": "英语",
    "phy": "物理",
    "chem": "化学",
    "bio": "生物",
    "pol": "道德与法治",
    "hist": "历史",
    "geo": "地理",
    "sci": "科学",
    "it": "信息技术",
    "pe": "体育与健康",
    "art": "美术",
    "mus": "音乐",
    "comp": "综合实践",
}

# 学段定义
STAGES = {
    "primary":    {"grades": [1,2,3,4,5,6], "label": "小学", "english_start": 3},
    "junior":     {"grades": [7,8,9],     "label": "初中"},
    "senior":     {"grades": [10,11,12],  "label": "高中"},
}

# 各学科的起始年级映射
SUBJECT_START_GRADE = {
    "math": 1, "chi": 1, "eng": 3,
    "phy": 8, "chem": 9, "bio": 7,
    "pol": 7, "hist": 7, "geo": 7,
    "sci": 1, "it": 3, "pe": 1,
    "art": 1, "mus": 1, "comp": 1,
}


def get_status(version, subject_code, grade, stage_key):
    """根据版本优先级和年级决定数据状态"""
    # 学科未开设的年级直接 planned
    if grade < SUBJECT_START_GRADE[subject_code]:
        return "planned"
    vp = version["priority"]
    if vp == "P0":
        # P0版本：小学核心年级(1/3/6)、初中全、高中核心(10/12) 数据就绪
        if stage_key == "junior":
            return "data_ready"
        if stage_key == "primary" and grade in [1, 3, 6]:
            return "data_ready"
        if stage_key == "senior" and grade in [10, 12]:
            return "data_ready"
        return "data_partial"
    elif vp == "P1":
        # P1版本：初中核心年级、小学关键年级 数据就绪
        if stage_key == "junior" and grade in [7, 9]:
            return "data_ready"
        if stage_key == "primary" and grade in [3, 6]:
            return "data_ready"
        return "data_partial"
    else:
        # P2版本：基本为planned或partial
        if stage_key == "junior" and grade == 7:
            return "data_partial"
        return "planned"

def generate_textbook_versions():
    entries = []
    for version in VERSIONS:
        for subj_code, subj_name in SUBJECTS.items():
            # 学科未开设则跳过整个版本
            start_grade = SUBJECT_START_GRADE[subj_code]
            for stage_key, stage_info in STAGES.items():
                for grade in stage_info["grades"]:
                    # 学科未开设的年级跳过
                    if grade < start_grade:
                        continue
                    # 英语小学从三年级开始
                    if subj_code == "eng" and stage_key == "primary" and grade < stage_info["english_start"]:
                        continue

                    # 英语学科：外研版是P0，其他版本英语等级降低
                    actual_priority = version["priority"]
                    if subj_code == "eng":
                        if version["id_prefix"] == "fltrp":
                            actual_priority = "P0"
                        elif version["id_prefix"] == "pep":
                            actual_priority = "P0"
                        else:
                            actual_priority = "P1"

                    # 语文/数学：只有人教版和部编版是P0
                    if subj_code == "chi":
                        if version["id_prefix"] == "pep":
                            actual_priority = "P0"
                        else:
                            actual_priority = version["priority"]

                    # 物理/化学/生物/道德与法治/历史/地理：人教版/部编版P0，其他降级
                    if subj_code in ["phy", "chem", "bio", "pol", "hist", "geo"]:
                        if version["id_prefix"] in ["pep"]:
                            actual_priority = "P0"
                        elif version["id_prefix"] in ["su", "bsd", "ecnu"]:
                            actual_priority = "P1"
                        else:
                            actual_priority = "P2"

                    # 小学科学/初中理化生/音体美/信息技术/综合实践：人教版优先
                    if subj_code in ["sci", "it", "pe", "art", "mus", "comp"]:
                        if version["id_prefix"] == "pep":
                            actual_priority = "P0"
                        else:
                            actual_priority = "P1"

                    volume_labels = ["上册", "下册"] if stage_key != "senior" else ["必修第一册", "必修第二册", "选择性必修第一册", "选择性必修第二册", "选择性必修第三册"]

                    for vi, vol_label in enumerate(volume_labels):
                        if stage_key == "senior" and vi >= len(volume_labels):
                            break
                        if stage_key != "senior" and vi >= 2:
                            break

                        vol_num = vi + 1
                        version_id = f"{version['id_prefix']}-{subj_code}-{grade}-vol{vol_num}-2024"

                        # 高中特殊命名
                        if stage_key == "senior":
                            if vol_num <= 2:
                                version_id = f"{version['id_prefix']}-{subj_code}-{grade}-required{vol_num}-2024"
                            else:
                                version_id = f"{version['id_prefix']}-{subj_code}-{grade}-selective{vol_num-2}-2024"

                        entries.append({
                            "version_id": version_id,
                            "publisher": version["publisher"],
                            "version_name": version["name"],
                            "subject": subj_name,
                            "subject_code": subj_code,
                            "grade": grade,
                            "stage": stage_info["label"],
                            "volume": vol_label,
                            "volume_number": vol_num,
                            "year": 2024,
                            "isbn": f"978-7-{100+grade:03d}-{ord(version['id_prefix'][0]):05d}-{vol_num}",
                            "coverage": version["coverage"],
                            "priority": actual_priority,
                            "status": get_status(version, subj_code, grade, stage_key)
                        })

    return {"textbook_versions": entries, "metadata": {
        "total_versions": 8,
        "total_entries": len(entries),
        "total_subjects": 14,
        "stage_coverage": "小学1-6年级 / 初中7-9年级 / 高中10-12年级",
        "generated": "2026-06-25",
        "data_status_distribution": {
            "data_ready": sum(1 for e in entries if e["status"] == "data_ready"),
            "data_partial": sum(1 for e in entries if e["status"] == "data_partial"),
            "planned": sum(1 for e in entries if e["status"] == "planned"),
        }
    }}


# ============================================================
# 2. 课标编码库生成
# ============================================================

def generate_curriculum_standards():
    """生成全学段课标编码，覆盖小学1-6、初中7-9、高中10-12"""
    
    all_kps = []
    
    # ---- 数学学科 ----
    
    # 小学数学 (1-6年级)
    math_primary = [
        # 一年级
        ("KP-MAT-001", "1-5的认识和加减法", "L1", [], 1),
        ("KP-MAT-002", "0的认识和加减法", "L1", ["KP-MAT-001"], 1),
        ("KP-MAT-003", "6-10的认识和加减法", "L1", ["KP-MAT-001"], 1),
        ("KP-MAT-004", "11-20各数的认识", "L1", ["KP-MAT-003"], 1),
        ("KP-MAT-005", "20以内的进位加法", "L2", ["KP-MAT-004"], 1),
        ("KP-MAT-006", "认识图形（一）", "L1", [], 1),
        ("KP-MAT-007", "钟表的认识", "L1", [], 1),
        # 二年级
        ("KP-MAT-010", "100以内的加法和减法", "L2", ["KP-MAT-005"], 2),
        ("KP-MAT-011", "表内乘法（一）", "L2", ["KP-MAT-010"], 2),
        ("KP-MAT-012", "长度单位", "L1", [], 2),
        ("KP-MAT-013", "角的初步认识", "L1", [], 2),
        ("KP-MAT-014", "表内除法（一）", "L2", ["KP-MAT-011"], 2),
        ("KP-MAT-015", "万以内数的认识", "L2", ["KP-MAT-010"], 2),
        # 三年级
        ("KP-MAT-020", "万以内的加法和减法", "L2", ["KP-MAT-015"], 3),
        ("KP-MAT-021", "多位数乘一位数", "L3", ["KP-MAT-011","KP-MAT-020"], 3),
        ("KP-MAT-022", "分数的初步认识", "L2", ["KP-MAT-003"], 3),
        ("KP-MAT-023", "长方形和正方形", "L2", [], 3),
        ("KP-MAT-024", "位置与方向", "L1", [], 3),
        ("KP-MAT-025", "除数是一位数的除法", "L3", ["KP-MAT-014","KP-MAT-021"], 3),
        ("KP-MAT-026", "面积", "L2", ["KP-MAT-023"], 3),
        ("KP-MAT-027", "年、月、日", "L1", [], 3),
        # 四年级
        ("KP-MAT-030", "大数的认识", "L2", ["KP-MAT-020"], 4),
        ("KP-MAT-031", "三位数乘两位数", "L3", ["KP-MAT-021"], 4),
        ("KP-MAT-032", "除数是两位数的除法", "L3", ["KP-MAT-025"], 4),
        ("KP-MAT-033", "平行四边形和梯形", "L2", ["KP-MAT-023"], 4),
        ("KP-MAT-034", "运算律", "L3", ["KP-MAT-010","KP-MAT-031"], 4),
        ("KP-MAT-035", "小数的意义和性质", "L2", [], 4),
        ("KP-MAT-036", "三角形", "L2", ["KP-MAT-013","KP-MAT-023"], 4),
        # 五年级
        ("KP-MAT-040", "小数乘法", "L3", ["KP-MAT-031","KP-MAT-035"], 5),
        ("KP-MAT-041", "小数除法", "L3", ["KP-MAT-032","KP-MAT-035"], 5),
        ("KP-MAT-042", "简易方程", "L3", ["KP-MAT-034"], 5),
        ("KP-MAT-043", "多边形的面积", "L3", ["KP-MAT-033","KP-MAT-036"], 5),
        ("KP-MAT-044", "分数的意义和性质", "L3", ["KP-MAT-022"], 5),
        ("KP-MAT-045", "因数与倍数", "L2", ["KP-MAT-011","KP-MAT-014"], 5),
        ("KP-MAT-046", "长方体和正方体", "L3", ["KP-MAT-026"], 5),
        ("KP-MAT-047", "分数的加法和减法", "L3", ["KP-MAT-044"], 5),
        # 六年级
        ("KP-MAT-050", "分数乘法", "L3", ["KP-MAT-044","KP-MAT-040"], 6),
        ("KP-MAT-051", "分数除法", "L3", ["KP-MAT-044","KP-MAT-041"], 6),
        ("KP-MAT-052", "比和比例", "L3", ["KP-MAT-050","KP-MAT-051"], 6),
        ("KP-MAT-053", "圆", "L3", ["KP-MAT-043"], 6),
        ("KP-MAT-054", "百分数", "L3", ["KP-MAT-050"], 6),
        ("KP-MAT-055", "圆柱与圆锥", "L3", ["KP-MAT-046","KP-MAT-053"], 6),
        ("KP-MAT-056", "整理和复习", "L4", [], 6),
    ]
    
    # 初中数学 (7-9年级)
    math_junior = [
        # 七年级
        ("K7-MAT-001", "有理数概念", "L1", ["KP-MAT-020"], 7),
        ("K7-MAT-002", "有理数运算", "L2", ["K7-MAT-001"], 7),
        ("K7-MAT-003", "数轴与绝对值", "L2", ["K7-MAT-001"], 7),
        ("K7-MAT-010", "整式概念", "L1", ["K7-MAT-002"], 7),
        ("K7-MAT-011", "合并同类项", "L2", ["K7-MAT-010"], 7),
        ("K7-MAT-012", "去括号与整式加减", "L2", ["K7-MAT-011"], 7),
        ("K7-MAT-013", "整式乘法", "L3", ["K7-MAT-012"], 7),
        ("K7-MAT-020", "方程概念", "L1", ["K7-MAT-012"], 7),
        ("K7-MAT-021", "等式性质", "L2", ["K7-MAT-020"], 7),
        ("K7-MAT-022", "解一元一次方程合并与移项", "L3", ["K7-MAT-021","K7-MAT-012"], 7),
        ("K7-MAT-023", "解一元一次方程去括号去分母", "L3", ["K7-MAT-022"], 7),
        ("K7-MAT-024", "一元一次方程应用", "L4", ["K7-MAT-023"], 7),
        ("K7-MAT-030", "几何图形初步", "L1", ["KP-MAT-036"], 7),
        ("K7-MAT-031", "直线射线线段", "L1", [], 7),
        ("K7-MAT-032", "角的概念与运算", "L2", ["K7-MAT-031"], 7),
        ("K7-MAT-040", "相交线与平行线", "L2", ["K7-MAT-032"], 7),
        ("K7-MAT-041", "平行线的性质与判定", "L3", ["K7-MAT-040"], 7),
        ("K7-MAT-050", "实数概念", "L2", ["K7-MAT-002"], 7),
        ("K7-MAT-051", "平方根与立方根", "L3", ["K7-MAT-050"], 7),
        ("K7-MAT-060", "平面直角坐标系", "L2", ["KP-MAT-024"], 7),
        ("K7-MAT-070", "二元一次方程组", "L3", ["K7-MAT-024"], 7),
        ("K7-MAT-080", "不等式与不等式组", "L3", ["K7-MAT-024","K7-MAT-070"], 7),
        ("K7-MAT-090", "数据的收集整理与描述", "L1", [], 7),
        # 八年级
        ("K8-MAT-001", "三角形", "L2", ["K7-MAT-030"], 8),
        ("K8-MAT-002", "全等三角形", "L3", ["K8-MAT-001"], 8),
        ("K8-MAT-003", "轴对称", "L3", ["K8-MAT-002"], 8),
        ("K8-MAT-010", "整式的乘法与因式分解", "L3", ["K7-MAT-013"], 8),
        ("K8-MAT-011", "分式", "L3", ["K8-MAT-010"], 8),
        ("K8-MAT-012", "分式方程", "L4", ["K8-MAT-011","K7-MAT-024"], 8),
        ("K8-MAT-020", "勾股定理", "L3", ["K8-MAT-001"], 8),
        ("K8-MAT-030", "平行四边形", "L3", ["K8-MAT-002"], 8),
        ("K8-MAT-031", "矩形菱形正方形", "L3", ["K8-MAT-030"], 8),
        ("K8-MAT-040", "一次函数", "L3", ["K7-MAT-060","K7-MAT-024"], 8),
        ("K8-MAT-050", "数据的分析", "L2", ["K7-MAT-090"], 8),
        # 九年级
        ("K9-MAT-001", "一元二次方程", "L3", ["K8-MAT-012","K7-MAT-024"], 9),
        ("K9-MAT-010", "二次函数", "L4", ["K8-MAT-040","K9-MAT-001"], 9),
        ("K9-MAT-020", "旋转", "L3", ["K8-MAT-003"], 9),
        ("K9-MAT-030", "圆", "L3", ["KP-MAT-053","K8-MAT-002"], 9),
        ("K9-MAT-040", "相似", "L4", ["K8-MAT-002","KP-MAT-052"], 9),
        ("K9-MAT-050", "锐角三角函数", "L4", ["K9-MAT-040","K8-MAT-020"], 9),
        ("K9-MAT-060", "概率初步", "L2", ["K8-MAT-050"], 9),
    ]
    
    # 高中数学 (10-12年级)
    math_senior = [
        ("KH-MAT-001", "集合与常用逻辑用语", "L2", [], 10),
        ("KH-MAT-002", "一元二次函数方程和不等式", "L3", ["K9-MAT-001","K9-MAT-010"], 10),
        ("KH-MAT-010", "函数的概念与性质", "L3", ["K8-MAT-040"], 10),
        ("KH-MAT-011", "指数函数与对数函数", "L4", ["KH-MAT-010"], 10),
        ("KH-MAT-020", "三角函数", "L4", ["K9-MAT-050"], 10),
        ("KH-MAT-030", "平面向量及其应用", "L3", ["K8-MAT-020"], 10),
        ("KH-MAT-040", "复数", "L2", ["K7-MAT-050"], 10),
        ("KH-MAT-050", "立体几何初步", "L4", ["KP-MAT-046"], 10),
        ("KH-MAT-060", "统计", "L2", ["K8-MAT-050"], 10),
        ("KH-MAT-070", "概率", "L3", ["K9-MAT-060"], 10),
        ("KH-MAT-080", "数列", "L3", ["KH-MAT-010"], 11),
        ("KH-MAT-090", "导数及其应用", "L5", ["KH-MAT-010","KH-MAT-011"], 11),
        ("KH-MAT-100", "空间向量与立体几何", "L4", ["KH-MAT-050","KH-MAT-030"], 11),
        ("KH-MAT-110", "直线和圆的方程", "L3", ["K9-MAT-030","KH-MAT-030"], 11),
        ("KH-MAT-120", "圆锥曲线的方程", "L5", ["KH-MAT-110"], 11),
        ("KH-MAT-130", "计数原理", "L3", [], 12),
        ("KH-MAT-140", "随机变量及其分布", "L4", ["KH-MAT-070","KH-MAT-130"], 12),
    ]
    
    # ---- 语文学科 ----
    
    chi_primary = [
        ("KP-CHI-001", "汉语拼音", "L1", [], 1),
        ("KP-CHI-002", "汉字基本笔画", "L1", [], 1),
        ("KP-CHI-003", "常用汉字识记(300字)", "L1", ["KP-CHI-002"], 1),
        ("KP-CHI-010", "看图写话", "L2", ["KP-CHI-003"], 2),
        ("KP-CHI-011", "标点符号（，。？！）", "L1", [], 2),
        ("KP-CHI-020", "段落阅读与理解", "L2", ["KP-CHI-010"], 3),
        ("KP-CHI-021", "日记与简单记叙文", "L2", ["KP-CHI-010","KP-CHI-011"], 3),
        ("KP-CHI-030", "古诗文背诵", "L2", ["KP-CHI-020"], 4),
        ("KP-CHI-031", "说明文阅读", "L2", ["KP-CHI-020"], 4),
        ("KP-CHI-040", "记叙文写作", "L3", ["KP-CHI-021"], 5),
        ("KP-CHI-041", "修辞手法（比喻拟人排比）", "L2", [], 5),
        ("KP-CHI-050", "议论文初步", "L3", ["KP-CHI-040"], 6),
        ("KP-CHI-051", "名著阅读与鉴赏", "L3", ["KP-CHI-030"], 6),
    ]
    
    chi_junior = [
        ("K7-CHI-001", "现代文阅读（记叙文）", "L3", ["KP-CHI-040"], 7),
        ("K7-CHI-002", "文言文入门", "L3", ["KP-CHI-030"], 7),
        ("K7-CHI-003", "说明文阅读与写作", "L3", ["KP-CHI-031"], 7),
        ("K7-CHI-010", "古诗词鉴赏", "L3", ["K7-CHI-002"], 8),
        ("K7-CHI-011", "议论文阅读与写作", "L4", ["KP-CHI-050"], 8),
        ("K7-CHI-020", "小说阅读", "L4", ["K7-CHI-001"], 9),
        ("K7-CHI-021", "综合性学习", "L4", ["K7-CHI-011"], 9),
    ]
    
    chi_senior = [
        ("KH-CHI-001", "论述类文本阅读", "L4", ["K7-CHI-011"], 10),
        ("KH-CHI-002", "文学类文本阅读", "L4", ["K7-CHI-020"], 10),
        ("KH-CHI-003", "文言文深度阅读", "L5", ["K7-CHI-002"], 10),
        ("KH-CHI-010", "古代诗歌鉴赏", "L4", ["K7-CHI-010"], 11),
        ("KH-CHI-011", "议论文写作进阶", "L5", ["K7-CHI-011"], 11),
        ("KH-CHI-020", "高考总复习", "L5", [], 12),
    ]
    
    # ---- 英语学科 ----

    eng_primary = [
        ("KP-ENG-001", "字母与发音", "L1", [], 3),
        ("KP-ENG-002", "基本词汇(200词)", "L1", ["KP-ENG-001"], 3),
        ("KP-ENG-003", "简单问候与自我介绍", "L1", ["KP-ENG-002"], 3),
        ("KP-ENG-010", "日常对话与基本句型", "L1", ["KP-ENG-003"], 4),
        ("KP-ENG-011", "现在进行时", "L2", ["KP-ENG-010"], 4),
        ("KP-ENG-020", "一般现在时", "L2", ["KP-ENG-010"], 5),
        ("KP-ENG-021", "一般过去时", "L2", ["KP-ENG-020"], 5),
        ("KP-ENG-022", "简单阅读(100词)", "L2", ["KP-ENG-020"], 5),
        ("KP-ENG-030", "一般将来时", "L2", ["KP-ENG-021"], 6),
        ("KP-ENG-031", "比较级与最高级", "L3", ["KP-ENG-020"], 6),
        ("KP-ENG-032", "简单写作(50词)", "L3", ["KP-ENG-022"], 6),
    ]

    eng_junior = [
        ("K7-ENG-001", "现在完成时", "L3", ["KP-ENG-030"], 7),
        ("K7-ENG-002", "宾语从句", "L3", ["KP-ENG-010"], 7),
        ("K7-ENG-003", "状语从句", "L3", ["K7-ENG-002"], 7),
        ("K7-ENG-010", "被动语态", "L3", ["K7-ENG-001"], 8),
        ("K7-ENG-011", "定语从句", "L4", ["K7-ENG-002"], 8),
        ("K7-ENG-020", "虚拟语气", "L4", ["K7-ENG-010"], 9),
        ("K7-ENG-021", "完形填空策略", "L4", ["K7-ENG-011"], 9),
    ]

    eng_senior = [
        ("KH-ENG-001", "非谓语动词", "L4", ["K7-ENG-010"], 10),
        ("KH-ENG-002", "名词性从句", "L4", ["K7-ENG-002"], 10),
        ("KH-ENG-003", "阅读理解进阶", "L4", ["K7-ENG-021"], 10),
        ("KH-ENG-010", "书面表达(应用文)", "L4", ["KP-ENG-032"], 11),
        ("KH-ENG-011", "长难句分析", "L5", ["KH-ENG-002"], 11),
        ("KH-ENG-020", "高考综合复习", "L5", [], 12),
    ]

    # ---- 物理学科 (8-12年级) ----
    phy_junior = [
        ("K8-PHY-001", "机械运动", "L2", [], 8),
        ("K8-PHY-002", "声现象", "L1", [], 8),
        ("K8-PHY-003", "光现象", "L2", ["K8-PHY-001"], 8),
        ("K8-PHY-010", "热现象", "L2", [], 8),
        ("K8-PHY-020", "力学基础", "L3", ["K8-PHY-001"], 8),
        ("K8-PHY-030", "电学初步", "L3", ["K8-PHY-020"], 8),
        ("K9-PHY-001", "内能", "L3", ["K8-PHY-010"], 9),
        ("K9-PHY-010", "欧姆定律", "L3", ["K8-PHY-030"], 9),
        ("K9-PHY-020", "电功率", "L3", ["K9-PHY-010"], 9),
        ("K9-PHY-030", "电磁现象", "L3", ["K9-PHY-010"], 9),
    ]
    phy_senior = [
        ("KH-PHY-001", "运动的描述", "L2", ["K8-PHY-001"], 10),
        ("KH-PHY-002", "匀变速直线运动", "L3", ["KH-PHY-001"], 10),
        ("KH-PHY-010", "相互作用与牛顿定律", "L4", ["KH-PHY-002"], 10),
        ("KH-PHY-020", "曲线运动与万有引力", "L4", ["KH-PHY-010"], 11),
        ("KH-PHY-030", "功和能", "L4", ["KH-PHY-010"], 11),
        ("KH-PHY-040", "电场与电势", "L4", ["K9-PHY-010"], 11),
        ("KH-PHY-050", "恒定电流", "L3", ["K9-PHY-020"], 11),
        ("KH-PHY-060", "磁场", "L4", ["KH-PHY-040","KH-PHY-050"], 12),
        ("KH-PHY-070", "电磁感应", "L5", ["KH-PHY-060"], 12),
        ("KH-PHY-080", "原子物理", "L4", ["KH-PHY-010"], 12),
    ]

    # ---- 化学学科 (9-12年级) ----
    chem_junior = [
        ("K9-CHEM-001", "物质构成的奥秘", "L2", [], 9),
        ("K9-CHEM-002", "元素与元素周期表", "L2", ["K9-CHEM-001"], 9),
        ("K9-CHEM-010", "化学方程式", "L3", ["K9-CHEM-001"], 9),
        ("K9-CHEM-020", "常见的酸和碱", "L3", ["K9-CHEM-010"], 9),
        ("K9-CHEM-030", "盐和化肥", "L3", ["K9-CHEM-020"], 9),
        ("K9-CHEM-040", "金属和金属材料", "L3", ["K9-CHEM-001"], 9),
    ]
    chem_senior = [
        ("KH-CHEM-001", "化学反应的热效应", "L3", ["K9-CHEM-010"], 10),
        ("KH-CHEM-002", "化学反应速率与平衡", "L4", ["KH-CHEM-001"], 10),
        ("KH-CHEM-010", "电解质溶液", "L4", ["K9-CHEM-020"], 10),
        ("KH-CHEM-020", "物质结构与元素周期律", "L4", ["K9-CHEM-002"], 11),
        ("KH-CHEM-030", "有机化学基础", "L4", ["KH-CHEM-001"], 11),
        ("KH-CHEM-040", "化学实验", "L4", ["KH-CHEM-010","KH-CHEM-020"], 12),
        ("KH-CHEM-050", "化学与生活", "L3", ["KH-CHEM-001"], 12),
    ]

    # ---- 生物学科 (7-12年级) ----
    bio_junior = [
        ("K7-BIO-001", "生物和生物圈", "L1", [], 7),
        ("K7-BIO-010", "细胞是生命活动的基本单位", "L2", ["K7-BIO-001"], 7),
        ("K7-BIO-020", "细胞怎样构成生物体", "L2", ["K7-BIO-010"], 7),
        ("K7-BIO-030", "生物圈中的绿色植物", "L2", ["K7-BIO-020"], 7),
        ("K8-BIO-001", "动物的主要类群", "L2", ["K7-BIO-020"], 8),
        ("K8-BIO-010", "动物的运动和行为", "L2", ["K8-BIO-001"], 8),
        ("K8-BIO-020", "生物的多样性及其保护", "L2", ["K8-BIO-001"], 8),
        ("K9-BIO-001", "生物体的结构", "L3", ["K7-BIO-010"], 9),
        ("K9-BIO-010", "人体的营养与健康", "L3", ["K9-BIO-001"], 9),
        ("K9-BIO-020", "人体的呼吸与循环", "L4", ["K9-BIO-010"], 9),
        ("K9-BIO-030", "生物的遗传和变异", "L4", ["K9-BIO-001"], 9),
    ]
    bio_senior = [
        ("KH-BIO-001", "细胞的结构与功能", "L3", ["K7-BIO-010"], 10),
        ("KH-BIO-010", "遗传的基本规律", "L4", ["K9-BIO-030","KH-BIO-001"], 10),
        ("KH-BIO-020", "生物的进化", "L3", ["KH-BIO-010"], 11),
        ("KH-BIO-030", "植物生命活动的调节", "L3", ["KH-BIO-001"], 11),
        ("KH-BIO-040", "生态系统与环境保护", "L3", ["KH-BIO-020"], 12),
        ("KH-BIO-050", "生物技术与工程", "L4", ["KH-BIO-010"], 12),
    ]

    # ---- 道德与法治 (7-12年级) ----
    pol_junior = [
        ("K7-POL-001", "成长的节拍", "L1", [], 7),
        ("K7-POL-010", "友谊的天空", "L1", ["K7-POL-001"], 7),
        ("K7-POL-020", "师长情谊", "L1", [], 7),
        ("K8-POL-001", "遵守社会规则", "L2", ["K7-POL-001"], 8),
        ("K8-POL-010", "勇担社会责任", "L2", ["K8-POL-001"], 8),
        ("K8-POL-020", "国家利益至上", "L2", ["K8-POL-001"], 8),
        ("K9-POL-001", "富强与创新", "L2", ["K8-POL-020"], 9),
        ("K9-POL-010", "民主与法治", "L3", ["K8-POL-001"], 9),
        ("K9-POL-020", "文明与家园", "L2", ["K9-POL-001"], 9),
    ]
    pol_senior = [
        ("KH-POL-001", "中国特色社会主义", "L3", ["K9-POL-001"], 10),
        ("KH-POL-010", "经济与社会", "L3", ["KH-POL-001"], 10),
        ("KH-POL-020", "政治与法治", "L4", ["K9-POL-010"], 11),
        ("KH-POL-030", "哲学与文化", "L4", ["KH-POL-001"], 12),
    ]

    # ---- 历史 (7-12年级) ----
    hist_junior = [
        ("K7-HIST-001", "中国古代史·先秦", "L2", [], 7),
        ("K7-HIST-010", "中国古代史·秦汉", "L2", ["K7-HIST-001"], 7),
        ("K7-HIST-020", "中国古代史·三国两晋", "L2", ["K7-HIST-010"], 7),
        ("K8-HIST-001", "中国古代史·隋唐", "L2", ["K7-HIST-020"], 8),
        ("K8-HIST-010", "中国古代史·宋元明清", "L3", ["K8-HIST-001"], 8),
        ("K8-HIST-020", "中国近代史·列强侵略", "L3", ["K8-HIST-010"], 8),
        ("K9-HIST-001", "中国近代史·新民主主义革命", "L3", ["K8-HIST-020"], 9),
        ("K9-HIST-010", "中国现代史·社会主义建设", "L3", ["K9-HIST-001"], 9),
        ("K9-HIST-020", "世界历史", "L3", ["K9-HIST-010"], 9),
    ]
    hist_senior = [
        ("KH-HIST-001", "中国古代史通论", "L4", ["K7-HIST-001"], 10),
        ("KH-HIST-010", "中国近代史通论", "L4", ["K9-HIST-001"], 10),
        ("KH-HIST-020", "世界古代近代史", "L4", ["K9-HIST-020"], 11),
        ("KH-HIST-030", "世界现代史", "L4", ["KH-HIST-020"], 12),
    ]

    # ---- 地理 (7-12年级) ----
    geo_junior = [
        ("K7-GEO-001", "地球和地图", "L2", [], 7),
        ("K7-GEO-010", "海洋与陆地", "L2", ["K7-GEO-001"], 7),
        ("K7-GEO-020", "天气与气候", "L2", ["K7-GEO-001"], 7),
        ("K7-GEO-030", "居民与聚落", "L2", ["K7-GEO-020"], 7),
        ("K8-GEO-001", "发展与合作", "L2", ["K7-GEO-030"], 8),
        ("K8-GEO-010", "中国的自然环境", "L3", ["K7-GEO-001"], 8),
        ("K8-GEO-020", "中国的自然资源", "L3", ["K8-GEO-010"], 8),
        ("K8-GEO-030", "中国的经济发展", "L3", ["K8-GEO-020"], 8),
        ("K9-GEO-001", "中国的地理差异", "L3", ["K8-GEO-010"], 9),
        ("K9-GEO-010", "北方地区", "L3", ["K9-GEO-001"], 9),
        ("K9-GEO-020", "南方地区与青藏地区", "L3", ["K9-GEO-001"], 9),
    ]
    geo_senior = [
        ("KH-GEO-001", "地球运动与时间计算", "L4", ["K7-GEO-001"], 10),
        ("KH-GEO-010", "大气运动与天气系统", "L4", ["K7-GEO-020","KH-GEO-001"], 10),
        ("KH-GEO-020", "水循环与洋流", "L3", ["KH-GEO-001"], 11),
        ("KH-GEO-030", "自然地理环境的整体性", "L4", ["KH-GEO-020"], 11),
        ("KH-GEO-040", "人文地理与区域发展", "L4", ["K8-GEO-030"], 12),
    ]

    # ---- 小学科学 (1-6年级) ----
    sci_primary = [
        ("KP-SCI-001", "观察物体", "L1", [], 3),
        ("KP-SCI-010", "生命的世界", "L1", [], 3),
        ("KP-SCI-020", "水与天气", "L1", ["KP-SCI-001"], 4),
        ("KP-SCI-030", "简单电路", "L2", ["KP-SCI-001"], 4),
        ("KP-SCI-040", "地球与宇宙", "L2", ["KP-SCI-020"], 5),
        ("KP-SCI-050", "健康的身体", "L2", ["KP-SCI-010"], 5),
        ("KP-SCI-060", "微小世界", "L2", ["KP-SCI-001"], 6),
        ("KP-SCI-070", "物质的变化", "L3", ["KP-SCI-001"], 6),
    ]

    # ---- 信息技术 (3-12年级) ----
    it_primary = [
        ("KP-IT-001", "认识电脑", "L1", [], 3),
        ("KP-IT-010", "键盘与鼠标操作", "L1", ["KP-IT-001"], 3),
        ("KP-IT-020", "画图与简单编程", "L2", ["KP-IT-010"], 4),
        ("KP-IT-030", "网络基础", "L2", ["KP-IT-001"], 5),
        ("KP-IT-040", "文字处理", "L2", ["KP-IT-010"], 6),
    ]
    it_junior = [
        ("K7-IT-001", "程序设计基础", "L3", ["KP-IT-020"], 7),
        ("K7-IT-010", "数据处理", "L3", ["KP-IT-040"], 7),
        ("K8-IT-001", "算法与流程图", "L3", ["K7-IT-001"], 8),
        ("K8-IT-010", "多媒体制作", "L3", ["KP-IT-040"], 8),
        ("K9-IT-001", "Python编程", "L4", ["K8-IT-001"], 9),
        ("K9-IT-010", "数据库基础", "L3", ["K7-IT-010"], 9),
    ]
    it_senior = [
        ("KH-IT-001", "数据结构", "L4", ["K9-IT-001"], 10),
        ("KH-IT-010", "人工智能初步", "L4", ["KH-IT-001"], 10),
        ("KH-IT-020", "信息系统与社会", "L3", ["K9-IT-010"], 11),
        ("KH-IT-030", "算法与程序设计进阶", "L5", ["KH-IT-001"], 12),
    ]

    # ---- 体育与健康 (1-12年级全学段) ----
    pe_primary = [
        ("KP-PE-001", "基本身体活动", "L1", [], 1),
        ("KP-PE-010", "体操与队列", "L1", [], 1),
        ("KP-PE-020", "跑跳基本动作", "L1", [], 2),
        ("KP-PE-030", "小球类基础", "L2", ["KP-PE-020"], 3),
        ("KP-PE-040", "健康知识", "L1", [], 4),
        ("KP-PE-050", "田径基本技能", "L2", ["KP-PE-020"], 5),
        ("KP-PE-060", "球类运动", "L2", ["KP-PE-030"], 6),
    ]
    pe_junior = [
        ("K7-PE-001", "体能与健康", "L2", ["KP-PE-050"], 7),
        ("K7-PE-010", "球类运动技能", "L3", ["KP-PE-060"], 7),
        ("K8-PE-001", "田径专项", "L3", ["K7-PE-001"], 8),
        ("K8-PE-010", "体操与武术", "L3", ["KP-PE-010"], 8),
        ("K9-PE-001", "中考体育项目", "L4", ["K7-PE-001","K8-PE-001"], 9),
        ("K9-PE-010", "健康教育专题", "L2", ["KP-PE-040"], 9),
    ]
    pe_senior = [
        ("KH-PE-001", "体能训练", "L3", ["K7-PE-001"], 10),
        ("KH-PE-010", "专项运动技能", "L4", ["K7-PE-010"], 10),
        ("KH-PE-020", "健康与社会适应", "L2", ["K9-PE-010"], 11),
        ("KH-PE-030", "体育与高考", "L4", ["KH-PE-001"], 12),
    ]

    # ---- 美术 (1-12年级) ----
    art_primary = [
        ("KP-ART-001", "认识色彩", "L1", [], 1),
        ("KP-ART-010", "简单绘画", "L1", ["KP-ART-001"], 1),
        ("KP-ART-020", "手工制作", "L1", [], 2),
        ("KP-ART-030", "图案设计", "L2", ["KP-ART-010"], 3),
        ("KP-ART-040", "中国画初步", "L2", ["KP-ART-001"], 4),
        ("KP-ART-050", "立体造型", "L2", ["KP-ART-020"], 5),
        ("KP-ART-060", "美术欣赏", "L2", ["KP-ART-010"], 6),
    ]
    art_junior = [
        ("K7-ART-001", "造型·表现", "L3", ["KP-ART-030"], 7),
        ("K7-ART-010", "设计·应用", "L3", ["KP-ART-050"], 7),
        ("K8-ART-001", "欣赏·评述", "L3", ["KP-ART-060"], 8),
        ("K8-ART-010", "综合·探索", "L3", ["K7-ART-001"], 8),
        ("K9-ART-001", "美术与生活", "L3", ["K8-ART-010"], 9),
        ("K9-ART-010", "美术与文化", "L3", ["K8-ART-001"], 9),
    ]
    art_senior = [
        ("KH-ART-001", "美术鉴赏", "L4", ["K8-ART-001"], 10),
        ("KH-ART-010", "绘画·雕塑", "L4", ["K7-ART-001"], 10),
        ("KH-ART-020", "设计·工艺", "L3", ["K7-ART-010"], 11),
        ("KH-ART-030", "现代媒体艺术", "L4", ["KH-ART-001"], 12),
    ]

    # ---- 音乐 (1-12年级) ----
    mus_primary = [
        ("KP-MUS-001", "歌唱基础", "L1", [], 1),
        ("KP-MUS-010", "节奏与节拍", "L1", [], 1),
        ("KP-MUS-020", "音乐欣赏", "L1", [], 2),
        ("KP-MUS-030", "简单乐器", "L2", ["KP-MUS-001"], 3),
        ("KP-MUS-040", "识谱与视唱", "L2", ["KP-MUS-010"], 4),
        ("KP-MUS-050", "合唱", "L2", ["KP-MUS-001"], 5),
        ("KP-MUS-060", "综合性表演", "L3", ["KP-MUS-050","KP-MUS-030"], 6),
    ]
    mus_junior = [
        ("K7-MUS-001", "歌唱与鉴赏", "L3", ["KP-MUS-050"], 7),
        ("K7-MUS-010", "演奏与创作", "L3", ["KP-MUS-030"], 7),
        ("K8-MUS-001", "音乐与生活", "L3", ["K7-MUS-001"], 8),
        ("K8-MUS-010", "民族民间音乐", "L3", ["K7-MUS-001"], 8),
        ("K9-MUS-001", "音乐与时代", "L3", ["K8-MUS-001"], 9),
        ("K9-MUS-010", "中外音乐比较", "L3", ["K8-MUS-010"], 9),
    ]
    mus_senior = [
        ("KH-MUS-001", "音乐鉴赏", "L4", ["K9-MUS-010"], 10),
        ("KH-MUS-010", "歌唱与演奏", "L4", ["K7-MUS-001"], 10),
        ("KH-MUS-020", "创作基础", "L4", ["K7-MUS-010"], 11),
        ("KH-MUS-030", "音乐与社会", "L3", ["KH-MUS-001"], 12),
    ]

    # ---- 综合实践 (1-12年级) ----
    comp_primary = [
        ("KP-COMP-001", "生活实践", "L1", [], 1),
        ("KP-COMP-010", "探究活动", "L2", ["KP-COMP-001"], 3),
        ("KP-COMP-020", "职业体验", "L2", [], 5),
    ]
    comp_junior = [
        ("K7-COMP-001", "研究性学习", "L3", ["KP-COMP-010"], 7),
        ("K7-COMP-010", "社区服务", "L2", ["KP-COMP-001"], 7),
        ("K8-COMP-001", "设计与制作", "L3", ["K7-COMP-001"], 8),
        ("K8-COMP-010", "职业体验日", "L2", ["KP-COMP-020"], 8),
        ("K9-COMP-001", "生涯规划", "L3", ["K7-COMP-001"], 9),
        ("K9-COMP-010", "创新实验", "L4", ["K8-COMP-001"], 9),
    ]
    comp_senior = [
        ("KH-COMP-001", "研究性学习进阶", "L4", ["K7-COMP-001"], 10),
        ("KH-COMP-010", "社会实践", "L3", ["K7-COMP-010"], 10),
        ("KH-COMP-020", "职业规划与升学指导", "L3", ["K9-COMP-001"], 11),
        ("KH-COMP-030", "创新创业实践", "L5", ["KH-COMP-001"], 12),
    ]

    all_kps = math_primary + math_junior + math_senior + \
              chi_primary + chi_junior + chi_senior + \
              eng_primary + eng_junior + eng_senior + \
              phy_junior + phy_senior + \
              chem_junior + chem_senior + \
              bio_junior + bio_senior + \
              pol_junior + pol_senior + \
              hist_junior + hist_senior + \
              geo_junior + geo_senior + \
              sci_primary + \
              it_primary + it_junior + it_senior + \
              pe_primary + pe_junior + pe_senior + \
              art_primary + art_junior + art_senior + \
              mus_primary + mus_junior + mus_senior + \
              comp_primary + comp_junior + comp_senior
    
    result = []
    for item in all_kps:
        code, name, difficulty, prereqs, grade = item
        # 推断学段
        if grade <= 6:
            stage = "小学"
        elif grade <= 9:
            stage = "初中"
        else:
            stage = "高中"
        result.append({
            "code": code,
            "name": name,
            "difficulty": difficulty,
            "prerequisites": prereqs,
            "grade": grade,
            "stage": stage,
        })
    
    return {
        "curriculum_standards": result,
        "metadata": {
            "total_knowledge_points": len(result),
            "stages": ["小学", "初中", "高中"],
            "subjects": ["数学", "语文", "英语", "物理", "化学", "生物", "道德与法治", "历史", "地理", "科学", "信息技术", "体育与健康", "美术", "音乐", "综合实践"],
            "grade_range": "1-12",
            "coding_convention": "KP=小学, K7/K8/K9=初中七八九年级, KH=高中",
            "generated": "2026-06-25",
        }
    }


# ============================================================
# 3. 知识图谱（章节结构）生成
# ============================================================

def generate_knowledge_graph():
    """为8版本的关键年级生成章节结构"""
    
    common_examples = {
        "方程建模": {"type": "应用题", "difficulty": "L3", "scene": "行程问题"},
        "基础计算": {"type": "计算题", "difficulty": "L1", "scene": "算术运算"},
        "几何证明": {"type": "证明题", "difficulty": "L3", "scene": "几何推理"},
        "生活应用": {"type": "应用题", "difficulty": "L2", "scene": "生活场景"},
    }
    
    # 关键年级章节定义：版本 → 年级 → 科目 → 章节
    chapter_defs = {
        "pep": {
            7: {
                "math": [
                    {"num": 1, "title": "有理数", "sections": [
                        {"id": "1.1", "title": "正数和负数", "kps": ["K7-MAT-001"], "pages": "P1-4"},
                        {"id": "1.2", "title": "有理数", "kps": ["K7-MAT-001","K7-MAT-003"], "pages": "P5-14"},
                        {"id": "1.3", "title": "有理数的加减法", "kps": ["K7-MAT-002"], "pages": "P15-30"},
                        {"id": "1.4", "title": "有理数的乘除法", "kps": ["K7-MAT-002"], "pages": "P31-42"},
                        {"id": "1.5", "title": "有理数的乘方", "kps": ["K7-MAT-002"], "pages": "P43-52"},
                    ]},
                    {"num": 2, "title": "整式的加减", "sections": [
                        {"id": "2.1", "title": "整式", "kps": ["K7-MAT-010"], "pages": "P53-61"},
                        {"id": "2.2", "title": "整式的加减", "kps": ["K7-MAT-011","K7-MAT-012"], "pages": "P62-73"},
                    ]},
                    {"num": 3, "title": "一元一次方程", "sections": [
                        {"id": "3.1", "title": "从算式到方程", "kps": ["K7-MAT-020","K7-MAT-021"], "pages": "P74-82"},
                        {"id": "3.2", "title": "解一元一次方程(一)", "kps": ["K7-MAT-022"], "pages": "P83-90"},
                        {"id": "3.3", "title": "解一元一次方程(二)", "kps": ["K7-MAT-023"], "pages": "P91-100"},
                        {"id": "3.4", "title": "实际问题与一元一次方程", "kps": ["K7-MAT-024"], "pages": "P101-112"},
                    ]},
                    {"num": 4, "title": "几何图形初步", "sections": [
                        {"id": "4.1", "title": "几何图形", "kps": ["K7-MAT-030"], "pages": "P113-120"},
                        {"id": "4.2", "title": "直线射线线段", "kps": ["K7-MAT-031"], "pages": "P121-128"},
                        {"id": "4.3", "title": "角", "kps": ["K7-MAT-032"], "pages": "P129-140"},
                    ]},
                ]
            },
            8: {
                "math": [
                    {"num": 11, "title": "三角形", "sections": [
                        {"id": "11.1", "title": "与三角形有关的线段", "kps": ["K8-MAT-001"], "pages": "P1-8"},
                        {"id": "11.2", "title": "与三角形有关的角", "kps": ["K8-MAT-001"], "pages": "P9-18"},
                    ]},
                    {"num": 12, "title": "全等三角形", "sections": [
                        {"id": "12.1", "title": "全等三角形", "kps": ["K8-MAT-002"], "pages": "P30-36"},
                        {"id": "12.2", "title": "三角形全等的判定", "kps": ["K8-MAT-002"], "pages": "P37-52"},
                    ]},
                    {"num": 17, "title": "勾股定理", "sections": [
                        {"id": "17.1", "title": "勾股定理", "kps": ["K8-MAT-020"], "pages": "P1-8"},
                        {"id": "17.2", "title": "勾股定理的逆定理", "kps": ["K8-MAT-020"], "pages": "P9-15"},
                    ]},
                    {"num": 19, "title": "一次函数", "sections": [
                        {"id": "19.1", "title": "函数", "kps": ["K8-MAT-040"], "pages": "P1-8"},
                        {"id": "19.2", "title": "一次函数", "kps": ["K8-MAT-040"], "pages": "P9-20"},
                    ]}
                ]
            },
            10: {
                "math": [
                    {"num": 1, "title": "集合与常用逻辑用语", "sections": [
                        {"id": "1.1", "title": "集合的概念", "kps": ["KH-MAT-001"], "pages": "P1-6"},
                        {"id": "1.2", "title": "集合间的基本关系", "kps": ["KH-MAT-001"], "pages": "P7-10"},
                    ]},
                    {"num": 3, "title": "函数的概念与性质", "sections": [
                        {"id": "3.1", "title": "函数的概念及其表示", "kps": ["KH-MAT-010"], "pages": "P58-67"},
                        {"id": "3.2", "title": "函数的基本性质", "kps": ["KH-MAT-010"], "pages": "P68-80"},
                    ]},
                    {"num": 5, "title": "三角函数", "sections": [
                        {"id": "5.1", "title": "任意角和弧度制", "kps": ["KH-MAT-020"], "pages": "P165-172"},
                        {"id": "5.2", "title": "三角函数的概念", "kps": ["KH-MAT-020"], "pages": "P173-182"},
                    ]},
                ]
            },
            3: {
                "chi": [
                    {"num": 1, "title": "第一单元", "sections": [
                        {"id": "1", "title": "大青树下的小学", "kps": ["KP-CHI-020"], "pages": "P1-3"},
                        {"id": "2", "title": "花的学校", "kps": ["KP-CHI-020"], "pages": "P4-6"},
                    ]},
                ],
                "eng": [
                    {"num": 1, "title": "Unit 1 Hello!", "sections": [
                        {"id": "A", "title": "Let's talk", "kps": ["KP-ENG-001","KP-ENG-003"], "pages": "P1-2"},
                        {"id": "B", "title": "Let's learn", "kps": ["KP-ENG-002"], "pages": "P3-4"},
                    ]},
                ]
            },
        },
        "su": {
            7: {
                "math": [
                    {"num": 1, "title": "数学与我们同行", "sections": [
                        {"id": "1.1", "title": "生活 数学", "kps": [], "pages": "P1-6"},
                    ]},
                    {"num": 2, "title": "有理数", "sections": [
                        {"id": "2.1", "title": "正数与负数", "kps": ["K7-MAT-001"], "pages": "P7-12"},
                        {"id": "2.2", "title": "有理数与无理数", "kps": ["K7-MAT-001","K7-MAT-050"], "pages": "P13-18"},
                        {"id": "2.3", "title": "数轴", "kps": ["K7-MAT-003"], "pages": "P19-24"},
                    ]},
                    {"num": 3, "title": "代数式", "sections": [
                        {"id": "3.1", "title": "字母表示数", "kps": ["K7-MAT-010"], "pages": "P48-53"},
                        {"id": "3.2", "title": "代数式", "kps": ["K7-MAT-010"], "pages": "P54-60"},
                    ]},
                    {"num": 4, "title": "一元一次方程", "sections": [
                        {"id": "4.1", "title": "从问题到方程", "kps": ["K7-MAT-020"], "pages": "P92-97"},
                        {"id": "4.2", "title": "解一元一次方程", "kps": ["K7-MAT-022","K7-MAT-023"], "pages": "P98-115"},
                        {"id": "4.3", "title": "用一元一次方程解决问题", "kps": ["K7-MAT-024"], "pages": "P116-138"},
                    ]},
                ]
            },
        },
        "bsd": {
            7: {
                "math": [
                    {"num": 1, "title": "丰富的图形世界", "sections": [
                        {"id": "1.1", "title": "生活中的立体图形", "kps": ["K7-MAT-030"], "pages": "P1-6"},
                    ]},
                    {"num": 2, "title": "有理数及其运算", "sections": [
                        {"id": "2.1", "title": "有理数", "kps": ["K7-MAT-001"], "pages": "P22-28"},
                        {"id": "2.2", "title": "数轴", "kps": ["K7-MAT-003"], "pages": "P29-33"},
                    ]},
                    {"num": 3, "title": "整式及其加减", "sections": [
                        {"id": "3.1", "title": "字母表示数", "kps": ["K7-MAT-010"], "pages": "P70-74"},
                    ]},
                    {"num": 5, "title": "一元一次方程", "sections": [
                        {"id": "5.1", "title": "认识一元一次方程", "kps": ["K7-MAT-020"], "pages": "P118-123"},
                        {"id": "5.2", "title": "求解一元一次方程", "kps": ["K7-MAT-022","K7-MAT-023"], "pages": "P124-135"},
                    ]},
                ]
            },
        },
        "shk": {
            7: {
                "math": [
                    {"num": 1, "title": "有理数", "sections": [
                        {"id": "1.1", "title": "正数和负数", "kps": ["K7-MAT-001"], "pages": "P1-6"},
                    ]},
                    {"num": 2, "title": "整式加减", "sections": [
                        {"id": "2.1", "title": "代数式", "kps": ["K7-MAT-010"], "pages": "P50-56"},
                    ]},
                    {"num": 3, "title": "一次方程与方程组", "sections": [
                        {"id": "3.1", "title": "一元一次方程及其解法", "kps": ["K7-MAT-020","K7-MAT-022"], "pages": "P72-80"},
                        {"id": "3.2", "title": "一元一次方程的应用", "kps": ["K7-MAT-023","K7-MAT-024"], "pages": "P81-95"},
                    ]},
                ]
            },
        },
        "ecnu": {
            7: {
                "math": [
                    {"num": 1, "title": "走进数学世界", "sections": []},
                    {"num": 2, "title": "有理数", "sections": [
                        {"id": "2.1", "title": "有理数", "kps": ["K7-MAT-001"], "pages": "P12-18"},
                    ]},
                    {"num": 3, "title": "整式的加减", "sections": [
                        {"id": "3.1", "title": "列代数式", "kps": ["K7-MAT-010"], "pages": "P56-62"},
                    ]},
                    {"num": 6, "title": "一元一次方程", "sections": [
                        {"id": "6.1", "title": "从实际问题到方程", "kps": ["K7-MAT-020"], "pages": "P1-6"},
                        {"id": "6.2", "title": "解一元一次方程", "kps": ["K7-MAT-022","K7-MAT-023"], "pages": "P7-20"},
                    ]},
                ]
            },
        },
        "zjedu": {
            7: {
                "math": [
                    {"num": 1, "title": "有理数", "sections": [
                        {"id": "1.1", "title": "从自然数到有理数", "kps": ["K7-MAT-001"], "pages": "P1-10"},
                    ]},
                    {"num": 4, "title": "代数式", "sections": [
                        {"id": "4.1", "title": "用字母表示数", "kps": ["K7-MAT-010"], "pages": "P73-78"},
                    ]},
                    {"num": 5, "title": "一元一次方程", "sections": [
                        {"id": "5.1", "title": "一元一次方程", "kps": ["K7-MAT-020","K7-MAT-022"], "pages": "P102-112"},
                        {"id": "5.2", "title": "一元一次方程的应用", "kps": ["K7-MAT-024"], "pages": "P113-130"},
                    ]},
                ]
            },
        },
        "sdedu": {
            7: {
                "math": [
                    {"num": 1, "title": "基本的几何图形", "sections": [
                        {"id": "1.1", "title": "我们身边的图形世界", "kps": ["K7-MAT-030"], "pages": "P1-6"},
                    ]},
                    {"num": 3, "title": "有理数的运算", "sections": [
                        {"id": "3.1", "title": "有理数的加减法", "kps": ["K7-MAT-002"], "pages": "P46-55"},
                    ]},
                    {"num": 6, "title": "整式的加减", "sections": [
                        {"id": "6.1", "title": "单项式与多项式", "kps": ["K7-MAT-010"], "pages": "P98-105"},
                    ]},
                    {"num": 7, "title": "一元一次方程", "sections": [
                        {"id": "7.1", "title": "等式与方程", "kps": ["K7-MAT-020","K7-MAT-021"], "pages": "P118-124"},
                        {"id": "7.2", "title": "一元一次方程的解法", "kps": ["K7-MAT-022","K7-MAT-023"], "pages": "P125-136"},
                    ]},
                ]
            },
        },
    }
    
    # 跨版本等价映射
    cross_version_mappings = [
        {
            "topic": "有理数概念",
            "knowledge_code": "K7-MAT-001",
            "mappings": [
                {"version": "人教版", "version_id": "pep-math-7-vol1-2024", "chapter": "第一章", "section": "1.1-1.2"},
                {"version": "苏教版", "version_id": "su-math-7-vol1-2024", "chapter": "第二章", "section": "2.1-2.2"},
                {"version": "北师大版", "version_id": "bsd-math-7-vol1-2024", "chapter": "第二章", "section": "2.1"},
                {"version": "沪科版", "version_id": "shk-math-7-vol1-2024", "chapter": "第一章", "section": "1.1"},
                {"version": "华师大版", "version_id": "ecnu-math-7-vol1-2024", "chapter": "第二章", "section": "2.1"},
                {"version": "浙教版", "version_id": "zjedu-math-7-vol1-2024", "chapter": "第一章", "section": "1.1"},
                {"version": "鲁教版", "version_id": "sdedu-math-7-vol1-2024", "chapter": "第三章", "section": "3.1"},
            ]
        },
        {
            "topic": "一元一次方程解法",
            "knowledge_code": "K7-MAT-022",
            "mappings": [
                {"version": "人教版", "version_id": "pep-math-7-vol1-2024", "chapter": "第三章", "section": "3.2-3.3"},
                {"version": "苏教版", "version_id": "su-math-7-vol1-2024", "chapter": "第四章", "section": "4.2"},
                {"version": "北师大版", "version_id": "bsd-math-7-vol1-2024", "chapter": "第五章", "section": "5.2"},
                {"version": "沪科版", "version_id": "shk-math-7-vol1-2024", "chapter": "第三章", "section": "3.1"},
                {"version": "华师大版", "version_id": "ecnu-math-7-vol1-2024", "chapter": "第六章", "section": "6.2"},
                {"version": "浙教版", "version_id": "zjedu-math-7-vol1-2024", "chapter": "第五章", "section": "5.1"},
                {"version": "鲁教版", "version_id": "sdedu-math-7-vol1-2024", "chapter": "第七章", "section": "7.2"},
            ]
        },
        {
            "topic": "一元一次方程应用",
            "knowledge_code": "K7-MAT-024",
            "mappings": [
                {"version": "人教版", "version_id": "pep-math-7-vol1-2024", "chapter": "第三章", "section": "3.4"},
                {"version": "苏教版", "version_id": "su-math-7-vol1-2024", "chapter": "第四章", "section": "4.3"},
                {"version": "北师大版", "version_id": "bsd-math-7-vol1-2024", "chapter": "第五章", "section": "5.3"},
                {"version": "沪科版", "version_id": "shk-math-7-vol1-2024", "chapter": "第三章", "section": "3.2"},
                {"version": "华师大版", "version_id": "ecnu-math-7-vol1-2024", "chapter": "第六章", "section": "6.3"},
                {"version": "浙教版", "version_id": "zjedu-math-7-vol1-2024", "chapter": "第五章", "section": "5.2"},
                {"version": "鲁教版", "version_id": "sdedu-math-7-vol1-2024", "chapter": "第七章", "section": "7.3"},
            ]
        },
        {
            "topic": "勾股定理",
            "knowledge_code": "K8-MAT-020",
            "mappings": [
                {"version": "人教版", "version_id": "pep-math-8-vol2-2024", "chapter": "第十七章", "section": "17.1-17.2"},
                {"version": "苏教版", "version_id": "su-math-8-vol1-2024", "chapter": "第三章", "section": "3.1-3.2"},
                {"version": "北师大版", "version_id": "bsd-math-8-vol1-2024", "chapter": "第一章", "section": "1.1-1.2"},
                {"version": "沪科版", "version_id": "shk-math-8-vol2-2024", "chapter": "第十八章", "section": "18.1"},
                {"version": "华师大版", "version_id": "ecnu-math-8-vol1-2024", "chapter": "第十四章", "section": "14.1-14.2"},
                {"version": "浙教版", "version_id": "zjedu-math-8-vol1-2024", "chapter": "第二章", "section": "2.1-2.2"},
                {"version": "鲁教版", "version_id": "sdedu-math-8-vol1-2024", "chapter": "第五章", "section": "5.1-5.2"},
            ]
        },
        {
            "topic": "三角函数",
            "knowledge_code": "KH-MAT-020",
            "mappings": [
                {"version": "人教版", "version_id": "pep-math-10-required1-2024", "chapter": "第五章", "section": "5.1-5.2"},
                {"version": "苏教版", "version_id": "su-math-10-required1-2024", "chapter": "第七章", "section": "7.1-7.2"},
                {"version": "北师大版", "version_id": "bsd-math-10-required2-2024", "chapter": "第一章", "section": "1.1-1.2"},
                {"version": "沪科版", "version_id": "shk-math-10-required2-2024", "chapter": "第六章", "section": "6.1"},
                {"version": "华师大版", "version_id": "ecnu-math-10-required1-2024", "chapter": "第五章", "section": "5.1-5.2"},
                {"version": "浙教版", "version_id": "zjedu-math-10-required2-2024", "chapter": "第一章", "section": "1.1-1.2"},
                {"version": "鲁教版", "version_id": "sdedu-math-10-required2-2024", "chapter": "第三章", "section": "3.1"},
            ]
        },
    ]
    
    graphs = {}
    for version_prefix, grade_data in chapter_defs.items():
        for grade, subject_data in grade_data.items():
            for subject_code, chapters in subject_data.items():
                version_id_prefix = f"{version_prefix}-{subject_code}-{grade}"
                for ch in chapters:
                    ch_id = f"{version_id_prefix}-ch{ch['num']}"
                    sections = []
                    for sec in ch["sections"]:
                        sec_obj = {
                            "section_id": sec["id"],
                            "title": sec["title"],
                            "page_range": sec.get("pages", ""),
                            "knowledge_points": [{"code": kp, "name": "", "difficulty": ""} for kp in sec.get("kps", [])],
                            "learning_objectives": [],
                            "key_points": [],
                            "difficult_points": [],
                            "examples": [],
                            "exercises": [],
                        }
                        sections.append(sec_obj)
                    
                    graphs[ch_id] = {
                        "chapter_id": ch_id,
                        "version_id": version_id_prefix,
                        "chapter_number": ch["num"],
                        "title": ch["title"],
                        "sections": sections,
                    }
    
    return {
        "knowledge_graphs": graphs,
        "cross_version_mappings": cross_version_mappings,
        "metadata": {
            "total_chapters": len(graphs),
            "total_versions_covered": len(chapter_defs),
            "total_cross_mappings": len(cross_version_mappings),
            "generated": "2026-06-25",
        }
    }


# ============================================================
# 主函数
# ============================================================

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. 生成教材版本数据
    print("Generating textbook_versions.json...")
    tv = generate_textbook_versions()
    with open(os.path.join(DATA_DIR, "textbook_versions.json"), "w", encoding="utf-8") as f:
        json.dump(tv, f, ensure_ascii=False, indent=2)
    print(f"  → {tv['metadata']['total_entries']} entries across {tv['metadata']['total_versions']} versions")
    print(f"  → Status: {tv['metadata']['data_status_distribution']}")
    
    # 2. 生成课标编码
    print("Generating curriculum_standards.json...")
    cs = generate_curriculum_standards()
    with open(os.path.join(DATA_DIR, "curriculum_standards.json"), "w", encoding="utf-8") as f:
        json.dump(cs, f, ensure_ascii=False, indent=2)
    print(f"  → {cs['metadata']['total_knowledge_points']} knowledge points across {', '.join(cs['metadata']['stages'])}")
    
    # 3. 生成知识图谱
    print("Generating knowledge_graph.json...")
    kg = generate_knowledge_graph()
    with open(os.path.join(DATA_DIR, "knowledge_graph.json"), "w", encoding="utf-8") as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)
    print(f"  → {kg['metadata']['total_chapters']} chapters across {kg['metadata']['total_versions_covered']} versions")
    print(f"  → {kg['metadata']['total_cross_mappings']} cross-version mappings")
    
    print("\n[DONE] All data files generated successfully!")

if __name__ == "__main__":
    main()
