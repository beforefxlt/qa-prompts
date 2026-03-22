---
name: prompt-debugging
description: Systematic workflow for debugging and optimizing LLM prompts, especially for vision/OCR tasks. Use when testing multiple models, iterating on prompts for structured JSON output, troubleshooting hallucinations, or optimizing output format for frontend rendering. Triggers: "prompt not working", "OCR results wrong", "model comparison", "output format issues", "hallucination", "try different models".
---

# Prompt Debugging Workflow

A systematic approach to diagnosing and fixing prompt issues, derived from real-world multi-model OCR debugging.

## When to Use

- Model produces incorrect/hallucinated output
- Structured JSON output is malformed
- Need to compare multiple models for a task
- Output formatting affects frontend display
- Vision/OCR tasks with specific requirements

## Core Workflow

### 1. Isolate the Problem

Create a **standalone test script** outside the main codebase:
```
experiments/
├── test_model_a.go
├── test_model_b.go  
└── verify_output_format.go
```

**Why?** Faster iteration, no service restarts, clear success/failure signals.

### 2. Model Selection Strategy

Evaluate models in order of capability for the task:

| Task Type | Recommended Order |
|-----------|-------------------|
| Math OCR | GLM-4V-Flash > Phi-3.5 > Llama-90b |
| General Vision | GPT-4V > Gemini-Flash > Phi-3.5 |
| Reasoning/Grading | GLM-4.7 > DeepSeek > GPT-4 |

**Red flags by model type:**
- **Hallucination**: Model sees what isn't there → Switch model
- **Repetitive output**: Model loops text → Reduce temperature or switch
- **Missing details**: Model skips content → Improve prompt specificity

### 3. Prompt Iteration Patterns

#### Pattern A: Role + Task + Constraints
```
Role: [Expert type].
Task: [Specific action].
Requirements:
1. [Constraint 1]
2. [Constraint 2]
Return: [Format specification]
```

#### Pattern B: Chinese Context (for Chinese output)
Use Chinese prompts for Chinese-output tasks—models follow language cues:
```
角色：数学OCR专家。
任务：识别印刷体题目和手写解答。
关键约束：
1. 符号区分：$\div$ vs $+$ vs $=$
2. 分数识别：$\frac{2}{5}$ 不是 $25$
返回 JSON：{"original_text": "...", "student_answer": "..."}
```

#### Pattern C: Aggressive Formatting Constraints
When output format affects UI rendering:
```
格式要求：
- 必须是**纯单行文本**
- 严禁包含换行符 (\n)
- 公式必须嵌入句子中，严禁单独成行
```

### 4. Verification Checklist

Before declaring success:

- [ ] Run standalone test script
- [ ] Check JSON parse success
- [ ] Verify no unwanted newlines: `strings.Contains(output, "\n")`
- [ ] Test on multiple input samples
- [ ] Verify frontend rendering if applicable

### 5. Documentation Pattern

After debugging, commit with detailed message:
```
feat: switch [component] to [new approach]

Debug process:
1. [Model A]: [Issue observed]
2. [Model B]: [Issue observed]
3. [Model C]: [Success/selected]

Changes:
- [Specific change 1]
- [Specific change 2]
```

## Common Pitfalls

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `$2/5$` → `$52$` | Vision model struggles with fractions | Switch to GLM-4V or add explicit constraint |
| Repeated text loops | Temperature too high or context confusion | Lower temperature, simplify prompt |
| Block-level LaTeX `$$` | Model defaults to display math | Explicitly request inline `$...$` |
| JSON parse failure | Model wraps in ```json | Use `cleanJSON()` to strip markdown |
| RESOURCE_EXHAUSTED | API quota limit | Switch provider or wait |

## Quick Reference

**Standalone test script template:**
```go
func main() {
    apiKey := os.Getenv("API_KEY")
    client := NewClient(apiKey)
    
    result, err := client.OCR(testImage)
    if err != nil {
        fmt.Println("FAIL:", err)
        return
    }
    
    // Verify structure
    if strings.Contains(result.Explanation, "\n") {
        fmt.Println("FAIL: Contains newlines")
    } else {
        fmt.Println("PASS")
    }
}
```
