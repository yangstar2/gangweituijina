"""
知识图谱查询引擎 —— 教师个性化备课 Skill 核心模块

以课标编码为桥梁，实现跨版本等价查询。
所有上层能力（备课、出题、错题变式）都依赖本模块。

版本ID格式: {publisher}-{subject}-{grade}-vol{num}-{year}
版本前缀格式: {publisher}-{subject}-{grade}（用于跨章节匹配）
"""

import json
import os
from typing import Dict, List, Optional, Any

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(filename: str) -> dict:
    """加载 JSON 数据文件（位于 Skill 根目录）"""
    path = os.path.join(SKILL_ROOT, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_textbook_data() -> dict:
    return _load_json("textbook_versions.json")


def _get_curriculum_data() -> dict:
    return _load_json("curriculum_standards.json")


def _get_knowledge_graph_data() -> dict:
    return _load_json("knowledge_graph.json")


def _version_prefix(version_id: str) -> str:
    """
    提取版本前缀，用于跨章节/跨版本匹配。
    
    "pep-math-7-vol1-2024" → "pep-math-7"
    "su-math-7-vol1-2024"  → "su-math-7"
    "pep-math-7"           → "pep-math-7" (已是前缀则原样返回)
    """
    # 如果版本ID已经不含 vol/year 后缀，直接返回
    # 否则从后往前剥离 volN-YYYY 段
    parts = version_id.rsplit("-", 2)
    if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
        return parts[0]
    return version_id


# ============================================================
# 核心 API
# ============================================================


def find_equivalent(knowledge_code: str, current_version: str) -> Optional[dict]:
    """
    跨版本等价查询
    
    Args:
        knowledge_code: 课标知识点编码，如 "K7-MAT-022"
        current_version: 当前教师使用的教材版本ID
    
    Returns:
        包含当前版本对应章节、页码、知识点详情，以及所有版本的映射
    """
    kg = _get_knowledge_graph_data()
    cs = _get_curriculum_data()
    
    # 1. 查找知识点详情
    kp_detail = None
    for kp in cs.get("curriculum_standards", []):
        if kp["code"] == knowledge_code:
            kp_detail = kp
            break
    
    if not kp_detail:
        return None
    
    # 2. 查找跨版本映射
    cross_mapping = None
    for mapping in kg.get("cross_version_mappings", []):
        if mapping["knowledge_code"] == knowledge_code:
            cross_mapping = mapping
            break
    
    # 3. 查找当前版本的具体章节
    current_chapter = None
    vprefix = _version_prefix(current_version)
    if cross_mapping:
        for m in cross_mapping["mappings"]:
            if m["version_id"].startswith(vprefix):
                current_chapter = m
                break
    
    # 4. 查找知识图谱中的具体章节数据
    chapter_detail = None
    for ch_id, ch_data in kg.get("knowledge_graphs", {}).items():
        if ch_data["version_id"].startswith(vprefix):
            for sec in ch_data.get("sections", []):
                for kp in sec.get("knowledge_points", []):
                    if kp["code"] == knowledge_code:
                        chapter_detail = {
                            "chapter_id": ch_id,
                            "chapter_number": ch_data["chapter_number"],
                            "chapter_title": ch_data["title"],
                            "section_id": sec["section_id"],
                            "section_title": sec["title"],
                            "page_range": sec.get("page_range", ""),
                        }
                        break
                if chapter_detail:
                    break
        if chapter_detail:
            break
    
    result = {
        "knowledge_code": knowledge_code,
        "knowledge_name": kp_detail["name"],
        "difficulty": kp_detail["difficulty"],
        "prerequisites": kp_detail.get("prerequisites", []),
        "grade": kp_detail.get("grade"),
        "stage": kp_detail.get("stage"),
        "current_version_mapping": current_chapter,
        "all_version_mappings": cross_mapping["mappings"] if cross_mapping else [],
        "current_chapter_detail": chapter_detail,
    }
    
    return result


def list_versions(subject: str = None, grade: int = None, stage: str = None) -> List[dict]:
    """
    列出所有教材版本，可按条件筛选

    Args:
        subject: 学科（数学/语文/英语/物理/化学/生物/道德与法治/历史/地理/科学/信息技术/体育与健康/美术/音乐/综合实践）
        grade: 年级（1-12）
        stage: 学段（小学/初中/高中）

    Returns:
        符合条件的版本列表
    """
    tv = _get_textbook_data()
    versions = tv.get("textbook_versions", [])

    if subject:
        # 同时支持学科名和学科代码
        subject_code_map = {
            "数学": "math", "语文": "chi", "英语": "eng",
            "物理": "phy", "化学": "chem", "生物": "bio",
            "道德与法治": "pol", "历史": "hist", "地理": "geo",
            "科学": "sci", "信息技术": "it",
            "体育与健康": "pe", "美术": "art", "音乐": "mus",
            "综合实践": "comp",
        }
        normalized = subject_code_map.get(subject, subject)
        versions = [v for v in versions
                    if v["subject"] == subject or v.get("subject_code") == normalized]
    if grade is not None:
        versions = [v for v in versions if v["grade"] == grade]
    if stage:
        versions = [v for v in versions if v["stage"] == stage]

    return versions


def get_chapter_structure(version_id: str) -> Optional[dict]:
    """
    获取指定版本的完整章节结构
    
    Args:
        version_id: 版本ID，如 "pep-math-7-vol1-2024"
    
    Returns:
        该版本所有章节的结构化数据
    """
    kg = _get_knowledge_graph_data()
    
    version_prefix = _version_prefix(version_id)
    chapters = []
    
    for ch_id, ch_data in kg.get("knowledge_graphs", {}).items():
        if ch_data["version_id"].startswith(version_prefix):
            chapters.append(ch_data)
    
    chapters.sort(key=lambda c: c["chapter_number"])
    
    if not chapters:
        return None
    
    tv = _get_textbook_data()
    version_meta = None
    for v in tv.get("textbook_versions", []):
        if v["version_id"] == version_id:
            version_meta = v
            break
    
    return {
        "version_id": version_id,
        "version_meta": version_meta,
        "total_chapters": len(chapters),
        "chapters": chapters,
    }


def find_prerequisites(knowledge_code: str) -> List[dict]:
    """
    递归查找知识点的所有前置依赖
    
    Args:
        knowledge_code: 课标知识点编码
    
    Returns:
        前置依赖链列表，按依赖层级排列
    """
    cs = _get_curriculum_data()
    
    kp_map = {kp["code"]: kp for kp in cs.get("curriculum_standards", [])}
    
    if knowledge_code not in kp_map:
        return []
    
    visited = set()
    result = []
    
    def dfs(code, depth=0):
        if code in visited:
            return
        visited.add(code)
        kp = kp_map.get(code)
        if not kp:
            return
        for prereq in kp.get("prerequisites", []):
            prereq_kp = kp_map.get(prereq)
            if prereq_kp:
                result.append({
                    "code": prereq,
                    "name": prereq_kp["name"],
                    "depth": depth + 1,
                })
                dfs(prereq, depth + 1)
    
    dfs(knowledge_code)
    return result


def validate_knowledge_points_in_range(
    knowledge_codes: List[str],
    version_id: str,
    current_section: str
) -> List[dict]:
    """
    校验知识点是否在指定章节范围内
    
    Args:
        knowledge_codes: 待校验的知识点编码列表
        version_id: 教材版本ID
        current_section: 当前章节ID
    
    Returns:
        校验结果列表，每个元素包含 code, allowed, reason
    """
    kg = _get_knowledge_graph_data()
    
    version_prefix = _version_prefix(version_id)
    
    # 收集该版本所有章节，按章节序号排序
    version_chapters = sorted(
        [(ch_id, ch_data) for ch_id, ch_data in kg.get("knowledge_graphs", {}).items()
         if ch_data["version_id"].startswith(version_prefix)],
        key=lambda x: x[1]["chapter_number"]
    )
    
    # 收集当前章节及之前已学章节的所有知识点
    allowed_kps = set()
    for ch_id, ch_data in version_chapters:
        for sec in ch_data.get("sections", []):
            for kp in sec.get("knowledge_points", []):
                allowed_kps.add(kp["code"])
        # 判断是否已到达当前目标章节
        section_ids = [s["section_id"] for s in ch_data.get("sections", [])]
        if current_section in section_ids:
            break
    
    results = []
    for code in knowledge_codes:
        if code in allowed_kps:
            results.append({"code": code, "allowed": True, "reason": ""})
        else:
            results.append({
                "code": code,
                "allowed": False,
                "reason": f"知识点 {code} 不在当前章节及之前已学范围内（超纲或未学）"
            })
    
    return results


def get_version_coverage_stats() -> dict:
    """
    获取教材版本覆盖统计
    
    Returns:
        版本覆盖统计数据
    """
    tv = _get_textbook_data()
    versions = tv.get("textbook_versions", [])
    
    stats = {
        "total_versions": 8,
        "total_entries": len(versions),
        "by_priority": {},
        "by_status": {},
        "by_stage": {},
        "by_subject": {},
        "by_version_name": {},
    }
    
    for v in versions:
        p = v["priority"]
        s = v["status"]
        stage = v["stage"]
        subj = v["subject"]
        vname = v["version_name"]
        
        stats["by_priority"][p] = stats["by_priority"].get(p, 0) + 1
        stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
        stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1
        stats["by_subject"][subj] = stats["by_subject"].get(subj, 0) + 1
        stats["by_version_name"][vname] = stats["by_version_name"].get(vname, 0) + 1
    
    return stats
