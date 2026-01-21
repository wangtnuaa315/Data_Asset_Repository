"""
导入案由类别 JSON 到数据库
用法: python scripts/legal/import_cause_tree.py
"""
import json
import asyncio
import asyncpg
from pathlib import Path

# 配置
JSON_FILE = Path(__file__).parent.parent.parent / "Instrument" / "案由类别.json"
DB_CONFIG = {
    'host': '192.168.2.170',
    'port': 5432,
    'user': 'admin',
    'password': 'Huaiye@2020**',
    'database': 'asset_catalog'
}


async def import_cause_tree():
    """导入案由树到数据库"""
    # 读取 JSON 文件
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"读取案由文件: {JSON_FILE}")
    print(f"顶层类别: {[item['name'] for item in data]}")
    
    # 连接数据库
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # 清空现有数据
        await conn.execute("DELETE FROM legal_cause_tree")
        print("已清空 legal_cause_tree 表")
        
        # 递归插入节点
        total_count = 0
        
        async def insert_node(node, case_type, parent_id, level, path_parts):
            nonlocal total_count
            
            current_path = " > ".join(path_parts + [node['name']])
            
            # 插入当前节点
            row = await conn.fetchrow("""
                INSERT INTO legal_cause_tree 
                (cause_name, case_type, parent_id, level, full_path, sort_order)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, node['name'], case_type, parent_id, level, current_path, total_count)
            
            node_id = row['id']
            total_count += 1
            
            # 递归插入子节点
            if node.get('children'):
                for child in node['children']:
                    await insert_node(
                        child, 
                        case_type, 
                        node_id, 
                        level + 1, 
                        path_parts + [node['name']]
                    )
        
        # 遍历顶层类别
        for item in data:
            case_type = item['name']
            print(f"导入类别: {case_type}")
            
            # 插入顶层节点
            row = await conn.fetchrow("""
                INSERT INTO legal_cause_tree 
                (cause_name, case_type, parent_id, level, full_path, sort_order)
                VALUES ($1, $2, NULL, 1, $3, $4)
                RETURNING id
            """, case_type, case_type, case_type, total_count)
            
            root_id = row['id']
            total_count += 1
            
            # 插入子节点
            if item.get('children'):
                for child in item['children']:
                    await insert_node(child, case_type, root_id, 2, [case_type])
        
        print(f"\n✅ 导入完成，共 {total_count} 个节点")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(import_cause_tree())
