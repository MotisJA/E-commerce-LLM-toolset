from flask import Flask, render_template, request, jsonify
from findbigV import find_bigV
from chatbot import ChatbotWithRetrieval
import json
from agents.marketing_agent import MarketingAgent
from agents.inventory_agent import InventoryAgent
from tools.inventory_tools import InventoryTools

# 实例化Flask应用
app = Flask(__name__)

# 初始化聊天机器人
bot = ChatbotWithRetrieval("docs")

# 初始化营销助手
marketing_agent = MarketingAgent()

# 初始化库存管理代理和工具
inventory_agent = InventoryAgent()
inventory_tools = InventoryTools()

# 主页路由，返回index.html模板
@app.route("/")
def index():
    return render_template("index.html")


# 处理请求的路由，仅允许POST请求
@app.route("/process", methods=["POST"])
def process():
    try:
        # 获取提交的花的名称
        flower = request.form["flower"]
        if not flower:
            raise ValueError("关键词不能为空")
            
        # 使用find_bigV函数获取相关数据
        response_str = find_bigV(flower=flower)
        # 使用json.loads将字符串解析为字典
        response = json.loads(response_str)

        # 返回数据的json响应
        return jsonify({
            "summary": response["summary"],
            "facts": response["facts"],
            "interest": response["interest"],
            "letter": response["letter"],
        })
        
    except Exception as e:
        print(f"Error in process: {str(e)}")
        return jsonify({
            "summary": "抱歉，服务器处理请求时出现错误",
            "facts": ["请检查输入是否正确", "稍后再试"],
            "interest": ["系统正在维护中", "请稍后再来"],
            "letter": ["非常抱歉，系统暂时无法处理您的请求。请稍后再试。"]
        }), 200  # 返回200而不是500，确保前端能正常处理


# 添加客服聊天接口
@app.route("/chat", methods=["POST"])
def chat():
    try:
        message = request.json.get("message", "")
        if not message:
            return jsonify({"error": "消息不能为空"}), 400
            
        response = bot.get_response(message)
        return jsonify({"response": response})
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({"error": "服务器处理请求时出现错误"}), 500


@app.route("/marketing/generate", methods=["POST"])
def generate_marketing_plan():
    try:
        data = request.json
        product = data.get("product")
        target = data.get("target")
        goal = data.get("goal")
        
        if not all([product, target, goal]):
            return jsonify({"error": "缺少必要参数"}), 400
            
        plan = marketing_agent.generate_marketing_plan(
            product=product,
            target=target,
            goal=goal
        )
        
        return jsonify({"plan": plan})
        
    except Exception as e:
        print(f"Error in generate_marketing_plan: {str(e)}")
        return jsonify({"error": "生成营销方案时出现错误"}), 500

@app.route("/marketing/refine", methods=["POST"])
def refine_marketing_plan():
    try:
        data = request.json
        initial_plan = data.get("plan")
        feedback = data.get("feedback")
        
        if not all([initial_plan, feedback]):
            return jsonify({"error": "缺少必要参数"}), 400
            
        refined_plan = marketing_agent.refine_plan(
            initial_plan=initial_plan,
            feedback=feedback
        )
        
        return jsonify({"plan": refined_plan})
        
    except Exception as e:
        print(f"Error in refine_marketing_plan: {str(e)}")
        return jsonify({"error": "优化营销方案时出现错误"}), 500


@app.route("/inventory/analyze", methods=["POST"])
def analyze_inventory():
    try:
        data = request.json
        product = data.get("product")
        current_stock = data.get("current_stock")
        
        if not all([product, current_stock]):
            return jsonify({"error": "缺少必要参数"}), 400
            
        # 获取影响因素
        factors = inventory_agent.analyze_factors(product)
        
        # 生成库存策略
        strategy = inventory_agent.generate_inventory_strategy(
            product=product,
            factors=factors,
            current_stock=current_stock
        )
        
        # 优化物流方案
        logistics = inventory_agent.optimize_logistics(strategy)
        
        # 更新历史记录
        inventory_agent.update_inventory_history({
            "product": product,
            "factors": factors,
            "strategy": strategy,
            "logistics": logistics
        })
        
        return jsonify({
            "factors": factors,
            "strategy": strategy,
            "logistics": logistics
        })
        
    except Exception as e:
        print(f"Error in analyze_inventory: {str(e)}")
        return jsonify({"error": "分析库存时出现错误"}), 500


# 判断是否是主程序运行，并设置Flask应用的host和debug模式
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
