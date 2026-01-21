import json

# 读取案由JSON
with open(r'd:\PythonProject\Data_Asset_Repository\Instrument\案由类别.json', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("案由类别结构分析")
print("=" * 60)

# 顶层类别
print("\n顶层类别(案件类型):")
for item in data:
    print(f"  - {item['name']}")

# 统计节点数
def count_nodes(nodes):
    total = 0
    for n in nodes:
        total += 1
        if n.get('children'):
            total += count_nodes(n['children'])
    return total

print(f"\n总案由节点数: {count_nodes(data)}")

# 计算最大深度
def max_depth(nodes, d=1):
    m = d
    for n in nodes:
        if n.get('children') and len(n['children']) > 0:
            m = max(m, max_depth(n['children'], d + 1))
    return m

print(f"最大树深度: {max_depth(data)} 级")

# 展示各类别的二级分类
print("\n各类别的二级分类:")
for item in data:
    print(f"\n【{item['name']}】")
    if item.get('children'):
        for child in item['children'][:5]:  # 只显示前5个
            print(f"  ├─ {child['name']}")
        if len(item['children']) > 5:
            print(f"  └─ ... 共 {len(item['children'])} 个二级分类")
