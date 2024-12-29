import random
from database.db import InventoryDB
from datetime import datetime
import json

def generate_random_product():
    """生成随机产品名称（限制长度不超过100字符）"""
    categories = {
        '花卉': ['玫瑰', '郁金香', '兰花', '向日葵', '牡丹', '百合', '菊花', '茉莉', '康乃馨', '薰衣草'],
        '服装': ['T恤', '衬衫', '连衣裙', '牛仔裤', '夹克', '毛衣', '西装', '裙子', '短裤', '风衣'],
        '电子': ['手机', '平板', '电脑', '耳机', '手表', '相机', '游戏机', '充电宝', '音箱', '路由器'],
        '食品': ['巧克力', '饼干', '茶叶', '咖啡', '坚果', '蜂蜜', '罐头', '调味品', '面包', '糖果'],
        '家居': ['枕头', '被子', '床单', '毛巾', '餐具', '灯具', '地毯', '窗帘', '收纳盒', '置物架']
    }
    
    category = random.choice(list(categories.keys()))
    product = f"{random.choice(categories[category])}-{category}-{random.choice(['A', 'B', 'C', 'D', 'E'])}"
    return product[:100]  # 确保不超过100字符

def generate_random_factors():
    """生成随机因素（限制JSON长度不超过1000字符）"""
    factors = {
        "需求": random.randint(50, 500),
        "效率": round(random.uniform(0.5, 1.0), 2),
        "成本": round(random.uniform(10.0, 100.0), 2),
        "季节": random.choice(['高', '中', '低'])
    }
    return json.dumps(factors, ensure_ascii=False)[:1000]

def generate_random_strategy():
    """生成随机策略（限制长度不超过500字符）"""
    strategy = {
        "定价": random.choice(['竞争', '溢价', '折扣']),
        "营销": random.choice(['广告', '社媒', '邮件', 'SEO']),
        "分销": random.choice(['直销', '批发', '零售']),
        "库存": random.choice(['JIT', '批量', '代发'])
    }
    return json.dumps(strategy, ensure_ascii=False)[:500]

def generate_random_logistics():
    """生成随机物流信息（限制长度不超过500字符）"""
    logistics = {
        "仓库": random.choice(['北京', '上海', '广州', '深圳', '成都']),
        "运输": random.choice(['空运', '海运', '陆运', '铁路']),
        "时效": random.randint(1, 30),
        "成本": round(random.uniform(10.0, 200.0), 2)
    }
    return json.dumps(logistics, ensure_ascii=False)[:500]

def main():
    db = InventoryDB()
    records = []
    timestamp = datetime.now().isoformat()[:50]  # 确保时间戳不超过50字符

    for i in range(100):
        record = {
            "timestamp": timestamp,
            "product": generate_random_product(),
            "factors": generate_random_factors(),
            "strategy": generate_random_strategy(),
            "logistics": generate_random_logistics()
        }
        records.append(record)
        print(f"准备添加记录 {i+1}/100: {record['product']}")

    try:
        db.add_records(records)
        print("成功批量添加 100 条记录到数据库。")
    except Exception as e:
        print(f"添加记录时出错: {e}")

if __name__ == "__main__":
    main()
