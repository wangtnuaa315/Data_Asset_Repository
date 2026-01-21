import pandas as pd

# 读取 Excel 文件
file_path = r'd:\PythonProject\Data_Asset_Repository\Instrument\蔡某某、李某某等案外人执行异议之诉民事申请再审审查民事案等.xlsx'
df = pd.read_excel(file_path)

print("=" * 60)
print("文件结构分析")
print("=" * 60)
print(f"总行数: {len(df)}")
print(f"总列数: {len(df.columns)}")

print("\n列名及数据类型:")
for col in df.columns:
    print(f"  - {col}: {df[col].dtype}")

print("\n前10行数据预览:")
print(df.head(10).to_string())

print("\n各列非空值统计:")
print(df.count())

print("\n各列唯一值数量:")
for col in df.columns:
    print(f"  {col}: {df[col].nunique()} 个唯一值")
