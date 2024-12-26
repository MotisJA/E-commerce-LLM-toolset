import random
from database.db import InventoryDB

def generate_random_product():
    """生成随机产品名称（花卉、服装等）"""
    categories = {
        '花卉': ['玫瑰', '郁金香', '兰花', '向日葵', '牡丹', '百合', '菊花', '茉莉', '康乃馨', '薰衣草'],
        '服装': ['T恤', '衬衫', '连衣裙', '牛仔裤', '夹克', '毛衣', '西装', '裙子', '短裤', '风衣'],
        '电子产品': ['智能手机', '平板电脑', '笔记本电脑', '耳机', '智能手表', '相机', '游戏机', '充电宝', '蓝牙音箱', '路由器'],
        '食品': ['巧克力', '饼干', '茶叶', '咖啡', '坚果', '蜂蜜', '罐头食品', '调味品', '面包', '糖果'],
        '家居用品': ['枕头', '被子', '床单', '毛巾', '餐具', '灯具', '地毯', '窗帘', '清洁剂', '收纳盒']
    }
    
    category = random.choice(list(categories.keys()))
    product = f"{random.choice(categories[category])} {random.choice(['A型', 'B型', 'C型', 'D型', 'E型'])}"
    return product

def generate_random_factors():
    """生成随机因素"""
    factors = {
        "市场需求": random.randint(50, 500),
        "供应链效率": round(random.uniform(0.5, 1.0), 2),
        "成本": round(random.uniform(10.0, 100.0), 2),
        "季节性": random.choice(['高', '中', '低'])
    }
    return factors

def generate_random_strategy():
    """生成随机策略"""
    strategies = [
        {"定价策略": random.choice(['竞争定价', '溢价定价', '折扣定价'])},
        {"营销策略": random.choice(['线上广告', '社交媒体', '电子邮件营销', '搜索引擎优化'])},
        {"分销策略": random.choice(['直销', '批发', '零售'])},
        {"库存策略": random.choice(['即时库存', '批量库存', '代发货'])}
    ]
    return random.choice(strategies)

def generate_random_logistics():
    """生成随机物流信息"""
    logistics = {
        "仓库位置": random.choice(['北京', '上海', '广州', '深圳', '成都']),
        "运输方式": random.choice(['空运', '海运', '陆运', '铁路']),
        "交货时间（天）": random.randint(1, 30),
        "单位成本（元）": round(random.uniform(10.0, 200.0), 2)
    }
    return logistics

def main():
    db = InventoryDB()
    records = []

    for i in range(100):
        record = {
            "product": generate_random_product(),
            "factors": generate_random_factors(),
            "strategy": generate_random_strategy(),
            "logistics": generate_random_logistics()
        }
        records.append(record)
        print(f"准备添加记录 {i+1}/100: {record['product']}")

    db.add_records(records)
    print("成功批量添加 100 条记录到数据库。")

if __name__ == "__main__":
    main()
