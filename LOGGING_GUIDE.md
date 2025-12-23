# 结构化日志使用指南 (Structured Logging Guide)

## 概述

语音判卷系统现已实现全流程结构化日志埋点，所有关键阶段都输出 **JSON 格式日志**，便于后期分析、问题定位和系统优化。

## 日志文件位置

日志文件按天自动切分：
```
logs/voice_marking-YYYY-MM-DD.log
```

示例：
- `logs/voice_marking-2025-12-23.log`
- `logs/voice_marking-2025-12-24.log`

## 日志格式

每条结构化日志都是 **有效的 JSON 对象**，包含以下标准字段：

```json
{
  "timestamp": "2025-12-23T10:38:05.521362",  // ISO 8601 时间戳
  "stage": "ASR_OUTPUT",                       // 处理阶段
  "logger": "src.speech",                      // 日志来源模块
  // ... 其他上下文特定字段
}
```

## 日志阶段 (Stages)

### 1. ASR_OUTPUT - 语音识别输出

**触发时机**: ASR 成功识别语音后

**字段**:
- `raw_input`: ASR 原始识别文本
- `engine`: 识别引擎 (如 "google")
- `confidence`: 识别置信度（如可用）

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.521362",
  "stage": "ASR_OUTPUT",
  "logger": "src.speech",
  "raw_input": "杨洋同学 对 18 错 2",
  "engine": "google"
}
```

**用途**:
- 统计 ASR 识别率
- 发现常见识别错误模式

---

### 2. TEXT_NORMALIZE - 文本归一化

**触发时机**: 文本清洗/归一化后

**字段**:
- `raw_input`: 原始输入
- `normalized_input`: 归一化后的文本
- `removed_tokens`: 被移除的词列表

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.522170",
  "stage": "TEXT_NORMALIZE",
  "logger": "src.parser",
  "raw_input": "杨洋同学  对  18  错  2",
  "normalized_input": "杨洋同学 对 18 错 2",
  "removed_tokens": ["extra_whitespace"]
}
```

**用途**:
- **发现新的噪声词候选**（如果某个词频繁出现但无意义）
- 验证文本清洗效果

---

### 3. PARSE_SUCCESS - 解析成功

**触发时机**: 成功从文本中提取姓名和分数

**字段**:
- `raw_input`: 原始输入
- `name`: 提取的姓名
- `correct`: 对的数量
- `wrong`: 错的数量

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.522308",
  "stage": "PARSE_SUCCESS",
  "logger": "src.parser",
  "raw_input": "杨洋同学  对  18  错  2",
  "name": "杨洋同学",
  "correct": 18,
  "wrong": 2
}
```

**用途**:
- 统计解析成功率
- 分析常见输入格式

---

### 4. PARSE_FAIL - 解析失败

**触发时机**: 无法从文本中提取有效信息

**字段**:
- `raw_input`: 原始输入
- `reason`: 失败原因
  - `missing_both_counts`: 既没有"对"也没有"错"
  - `no_name_extracted`: 无法提取姓名
- `missing_fields`: 缺失字段列表

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.522399",
  "stage": "PARSE_FAIL",
  "logger": "src.parser",
  "raw_input": "这是无效输入",
  "reason": "missing_both_counts",
  "missing_fields": ["correct", "wrong"]
}
```

**用途**:
- **关键：识别最常见的解析失败原因**
- 改进解析正则表达式
- 统计哪种格式失败最多

---

### 5. NAME_MATCH_EXACT - 精确姓名匹配

**触发时机**: 输入姓名与学生名单精确匹配

**字段**:
- `input_name`: 输入姓名
- `matched_name`: 匹配的学生姓名

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.522596",
  "stage": "NAME_MATCH_EXACT",
  "logger": "src.name_matcher",
  "input_name": "杨洋",
  "matched_name": "杨洋"
}
```

---

### 6. NAME_MATCH_PINYIN_EXACT - 拼音精确匹配

**触发时机**: 拼音完全匹配

**字段**:
- `input_name`: 输入姓名
- `input_pinyin`: 输入拼音
- `matched_name`: 匹配的学生姓名
- `matched_pinyin`: 学生姓名拼音

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.522640",
  "stage": "NAME_MATCH_PINYIN_EXACT",
  "logger": "src.name_matcher",
  "input_name": "yangyang",
  "input_pinyin": "yangyang",
  "matched_name": "杨洋",
  "matched_pinyin": "yangyang"
}
```

---

### 7. NAME_MATCH_PINYIN_CONTAINS - 拼音包含匹配

**触发时机**: 拼音部分匹配（新增）

**字段**:
- `input_name`: 输入姓名
- `input_pinyin`: 输入拼音
- `matched_name`: 匹配的学生姓名
- `matched_pinyin`: 学生姓名拼音

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.522680",
  "stage": "NAME_MATCH_PINYIN_CONTAINS",
  "logger": "src.name_matcher",
  "input_name": "wangxiao",
  "input_pinyin": "wangxiao",
  "matched_name": "王小明",
  "matched_pinyin": "wangxiaoming"
}
```

---

### 8. NAME_MATCH_FUZZY - 模糊匹配成功

**触发时机**: 通过编辑距离模糊匹配成功

**字段**:
- `input_name`: 输入姓名
- `input_pinyin`: 输入拼音
- `matched_name`: 最终匹配的学生姓名
- `candidate_count`: 候选数量
- `candidates`: **所有候选者列表**（非常重要！）
  - 每个候选包含 `name` 和 `distance`

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.523040",
  "stage": "NAME_MATCH_FUZZY",
  "logger": "src.name_matcher",
  "input_name": "yanyang",
  "input_pinyin": "yanyang",
  "matched_name": "杨洋",
  "candidate_count": 1,
  "candidates": [
    {"name": "杨洋", "distance": 1}
  ]
}
```

**用途**:
- **分析哪些学生名经常需要模糊匹配**
- 决定是否需要添加别名映射

---

### 9. NAME_MATCH_AMBIGUOUS - 歧义匹配

**触发时机**: 有多个相同编辑距离的候选

**字段**:
- `input_name`: 输入姓名
- `input_pinyin`: 输入拼音
- `candidate_count`: 候选数量
- `candidates`: 所有歧义候选列表

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.523100",
  "stage": "NAME_MATCH_AMBIGUOUS",
  "logger": "src.name_matcher",
  "input_name": "李明",
  "input_pinyin": "liming",
  "candidate_count": 2,
  "candidates": [
    {"name": "李明", "distance": 0},
    {"name": "黎明", "distance": 0}
  ]
}
```

**用途**:
- 发现同音名冲突
- 提示老师需要说全名

---

### 10. NAME_MATCH_FAIL - 姓名匹配失败

**触发时机**: 无法匹配到任何学生

**字段**:
- `input_name`: 输入姓名
- `input_pinyin`: 输入拼音
- `top_candidates`: 最接近的前 3 个候选（即使超出阈值）

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.523205",
  "stage": "NAME_MATCH_FAIL",
  "logger": "src.name_matcher",
  "input_name": "不存在的人",
  "input_pinyin": "bucunzairen",
  "top_candidates": [
    {"name": "张三", "distance": 9},
    {"name": "杨洋", "distance": 10},
    {"name": "李四", "distance": 10}
  ]
}
```

**用途**:
- **关键：识别最常失败的姓名识别模式**
- 通过 `top_candidates` 反推可能的正确学生
- 发现哪些学生名特别难识别

---

### 11. CSV_UPDATE_SUCCESS - CSV 更新成功

**触发时机**: 成功更新学生成绩

**字段**:
- `student_name`: 学生姓名
- `correct_delta`: 对的数量变化
- `wrong_delta`: 错的数量变化
- `new_correct`: 新的对的总数
- `new_wrong`: 新的错的总数

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.533747",
  "stage": "CSV_UPDATE_SUCCESS",
  "logger": "src.csv_updater",
  "student_name": "杨洋",
  "correct_delta": 2,
  "wrong_delta": 3,
  "new_correct": 20,
  "new_wrong": 5
}
```

**用途**:
- 统计更新频率
- 追踪成绩变化历史

---

### 12. CSV_UPDATE_FAIL - CSV 更新失败

**触发时机**: CSV 更新失败

**字段**:
- `student_name`: 学生姓名
- `reason`: 失败原因
  - `student_not_found`: 学生不在 CSV 中
  - `exception: ...`: 其他异常

**示例**:
```json
{
  "timestamp": "2025-12-23T10:38:05.534202",
  "stage": "CSV_UPDATE_FAIL",
  "logger": "src.csv_updater",
  "student_name": "不存在的学生",
  "reason": "student_not_found"
}
```

---

## 日志分析实战

### 1. 提取所有结构化日志

```bash
cat logs/voice_marking-2025-12-23.log | grep '{"timestamp"'
```

### 2. 统计各阶段日志数量

```bash
cat logs/voice_marking-2025-12-23.log | grep '{"timestamp"' | \
  jq -r '.stage' | sort | uniq -c | sort -rn
```

**输出示例**:
```
  150 PARSE_SUCCESS
   45 NAME_MATCH_EXACT
   30 NAME_MATCH_PINYIN_EXACT
   15 NAME_MATCH_FUZZY
   10 PARSE_FAIL
    5 NAME_MATCH_FAIL
```

### 3. 查看所有解析失败的原因

```bash
cat logs/voice_marking-2025-12-23.log | grep 'PARSE_FAIL' | \
  jq -r '"\(.reason): \(.raw_input)"'
```

**输出示例**:
```
missing_both_counts: 杨洋
no_name_extracted: 对 18 错 2
missing_both_counts: 听不清楚
```

### 4. 查找最常失败的姓名识别模式

```bash
cat logs/voice_marking-2025-12-23.log | grep 'NAME_MATCH_FAIL' | \
  jq -r '"\(.input_name) -> \(.input_pinyin)"' | \
  sort | uniq -c | sort -rn | head -10
```

**用途**: 发现哪些学生名总是识别失败，考虑添加别名映射。

### 5. 分析模糊匹配中的候选分布

```bash
cat logs/voice_marking-2025-12-23.log | grep 'NAME_MATCH_FUZZY' | \
  jq -r '.candidates[] | "\(.name): \(.distance)"' | \
  sort | uniq -c | sort -rn
```

**用途**: 了解哪些学生名经常作为模糊匹配候选出现。

### 6. 查看某个学生的所有成绩更新历史

```bash
cat logs/voice_marking-*.log | grep 'CSV_UPDATE_SUCCESS' | \
  jq -r 'select(.student_name == "杨洋") |
    "\(.timestamp): +\(.correct_delta)对 +\(.wrong_delta)错 -> 总计 \(.new_correct)对 \(.new_wrong)错"'
```

### 7. 统计 ASR 识别到的噪声词

```bash
cat logs/voice_marking-2025-12-23.log | grep 'TEXT_NORMALIZE' | \
  jq -r '.removed_tokens[]' | sort | uniq -c | sort -rn
```

**用途**: 发现需要添加到 `NAME_NOISE_WORDS` 的新词。

### 8. 完整流程追踪（单次输入）

```bash
# 获取某个时间点前后 5 秒的所有日志
cat logs/voice_marking-2025-12-23.log | grep '10:38:05' | \
  jq -r '"\(.stage): \(.raw_input // .input_name // .student_name)"'
```

**输出示例**:
```
ASR_OUTPUT: 杨洋同学 对 18 错 2
TEXT_NORMALIZE: 杨洋同学  对  18  错  2
PARSE_SUCCESS: 杨洋同学  对  18  错  2
NAME_MATCH_EXACT: 杨洋
CSV_UPDATE_SUCCESS: 杨洋
```

---

## 进阶分析：发现噪声词

### 方法 1: 对比 raw_input vs normalized_input

```bash
cat logs/voice_marking-*.log | grep 'TEXT_NORMALIZE' | \
  jq -r 'select(.raw_input != .normalized_input) |
    "原始: \(.raw_input)\n清洗: \(.normalized_input)\n---"' | \
  head -20
```

### 方法 2: 统计解析失败中的高频词

```bash
cat logs/voice_marking-*.log | grep 'PARSE_FAIL' | \
  jq -r '.raw_input' | \
  tr ' ' '\n' | \
  grep -v '^$' | \
  sort | uniq -c | sort -rn | head -20
```

如果看到某个词频繁出现在失败日志中，可能需要：
1. 添加到 `NAME_NOISE_WORDS`
2. 或改进 Parser 正则表达式

---

## 性能监控

### 统计每个阶段的失败率

```bash
#!/bin/bash
log_file="logs/voice_marking-2025-12-23.log"

parse_success=$(cat $log_file | grep 'PARSE_SUCCESS' | wc -l)
parse_fail=$(cat $log_file | grep 'PARSE_FAIL' | wc -l)
parse_total=$((parse_success + parse_fail))

name_success=$(cat $log_file | grep -E 'NAME_MATCH_(EXACT|PINYIN_EXACT|PINYIN_CONTAINS|FUZZY)' | wc -l)
name_fail=$(cat $log_file | grep -E 'NAME_MATCH_(FAIL|AMBIGUOUS)' | wc -l)
name_total=$((name_success + name_fail))

echo "解析成功率: $parse_success / $parse_total = $(awk "BEGIN {print $parse_success*100/$parse_total}")%"
echo "姓名匹配成功率: $name_success / $name_total = $(awk "BEGIN {print $name_success*100/$name_total}")%"
```

---

## 建议的日志保留策略

- **实时日志**: 保留最近 7 天
- **归档日志**: 压缩后保留 30 天
- **长期分析**: 提取关键统计数据到数据库

```bash
# 压缩 7 天前的日志
find logs/ -name "voice_marking-*.log" -mtime +7 -exec gzip {} \;

# 删除 30 天前的压缩日志
find logs/ -name "voice_marking-*.log.gz" -mtime +30 -delete
```

---

## 禁用结构化日志

如果不需要结构化日志，可以在 `config.py` 中设置：

```python
ENABLE_STRUCTURED_LOGGING = False
```

系统将只输出传统的文本日志，性能会有少许提升。

---

## 总结

结构化日志埋点的核心价值：

1. **可量化的改进**: 通过统计失败率明确优化方向
2. **噪声词发现**: 自动识别需要过滤的新词
3. **系统演进**: 基于数据决定是否需要 alias 映射、改进正则等
4. **问题定位**: 快速追踪单次输入的完整处理流程

所有日志都是有效 JSON，可以直接导入数据库或使用 `jq`/`pandas` 进行分析。
