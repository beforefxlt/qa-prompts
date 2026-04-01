import re
import yaml
import os

spec_file = "family_health_record_app/docs/specs/test_strategy_matrix.md"
output_file = "family_health_record_app/traceability.yaml"

def parse_specs():
    with open(spec_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 正则提取 TC-Px-xxx, 标题, 优先级, 分类标签
    # 示例: | TC-P1-001 | 首次打开应用，无成员时展示空状态引导页 | P1 | E2E/前端 | ... |
    pattern = r"\| (TC-P(\d)-\d+) \| (.*?) \| (P\d) \| (.*?) \|"
    matches = re.findall(pattern, content)

    traceability_data = []
    for tc_id, level_num, title, level, category in matches:
        traceability_data.append({
            "tc_id": tc_id.strip(),
            "level": level.strip(),
            "title": title.strip(),
            "category": category.strip(),
            "spec_source": "test_strategy_matrix.md",
            "test_file": "",
            "test_name": "",
            "code_paths": [],
            "status": "pending"
        })
    
    return traceability_data

if __name__ == "__main__":
    if os.path.exists(spec_file):
        data = parse_specs()
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"成功导出 {len(data)} 条用例到 {output_file}")
    else:
        print(f"找不到规格文件: {spec_file}")
