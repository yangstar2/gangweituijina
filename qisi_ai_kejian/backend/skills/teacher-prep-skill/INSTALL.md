# 安装说明

## 快速上手（3 步）

### 第 1 步：解压
将 `teacher-prep-skill.zip` 解压到任意目录，例如：
- Windows: `C:\Users\你的用户名\skills\teacher-prep-skill\`
- macOS: `~/skills/teacher-prep-skill/`
- Linux: `~/skills/teacher-prep-skill/`

### 第 2 步：导入到 AI 平台
在你常用的 AI 平台选择"导入本地 Skill / 加载本地 Skill"，指向 `teacher-prep-skill/` 目录。

支持的平台包括 WorkBuddy、Claude、ChatGPT、Coze、智谱、Cursor、Cline 等所有支持 SKILL.md 规范的 Agent 平台。

### 第 3 步：开始使用
在 AI 对话框里直接说人话即可：

```
帮我备一节人教版七年级上册第 3 章《一元一次方程》第 2 课时的课。
班级 42 人，期中考试本章正确率 65%。
我比较喜欢「讲练结合 + 小组讨论」的风格。
```

AI 会自动读取教材版本库、知识图谱、课标数据，生成 3 版教案供你选择。

## 系统要求

- 任何现代 AI Agent 平台（无需联网获取数据，所有数据本地化）
- Python 3.8+ （仅当你需要运行单元测试或重新生成数据时才需要）

## 包含的依赖

教学 Skill 运行时**零依赖**——AI 直接读取 JSON 数据 + Markdown 模板。

如果你想运行单元测试或重新生成数据：
```bash
pip install -r requirements.txt
python scripts/generate_data.py
```

## 验证安装

装上 Skill 后，试着对 AI 说：
```
我下学期要教 8 个班的初二物理，班级基础参差不齐，
我应该用你帮我做什么？
```

如果 AI 提到了"智能备课/学情看板/错题变式/应急救场"等关键词，说明 Skill 加载成功。

## 卸载

直接删除 `teacher-prep-skill/` 目录即可，无系统残留。

## 反馈

遇到问题或需要新增学科/版本支持：
- 提交 GitHub Issue
- 或在 SkillHub 平台评论区留言
