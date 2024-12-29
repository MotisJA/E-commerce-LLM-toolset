from flask import Flask, render_template, request, jsonify
from findbigV import find_bigV
from chatbot import ChatbotWithRetrieval
import json
from agents.marketing_agent import MarketingAgent
from agents.inventory_agent import InventoryAGI
from flask_cors import CORS

# 实例化Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 初始化聊天机器人
bot = ChatbotWithRetrieval("docs")

# 初始化营销助手
marketing_agent = MarketingAgent()

# 使用工厂方法初始化库存代理
inventory_agi = InventoryAGI.create_default_agent()

# 主页路由，返回index.html模板
@app.route("/")
def index():
    return render_template("index.html")


# 处理请求的路由，仅允许POST请求
@app.route("/process", methods=["POST"])
def process():
    try:
        category = request.form["category"]  # 使用新的参数名
        if not category:
            return jsonify({"error": "类目不能为空"}), 400
            
        response_str = find_bigV(category=category)
        response = json.loads(response_str)

        return jsonify(response)
        
    except Exception as e:
        print(f"Error in process: {str(e)}")
        return jsonify({
            "error": "服务器处理请求时出现错误",
            "details": str(e)
        }), 500


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
            
        # 生成营销方案 - CAMEL框架会返回对话式的营销方案
        result = marketing_agent.generate_marketing_plan(
            product=product,
            target=target,
            goal=goal
        )
        
        # 直接返回结构化的对话数据
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in generate_marketing_plan: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "conversation": []
        }), 500

@app.route("/marketing/refine", methods=["POST"])
def refine_marketing_plan():
    try:
        data = request.json
        initial_plan = data.get("plan")
        feedback = data.get("feedback")
        
        if not all([initial_plan, feedback]):
            return jsonify({"error": "缺少必要参数"}), 400
            
        # 优化营销方案
        result = marketing_agent.refine_plan(
            initial_plan=initial_plan,
            feedback=feedback
        )
        
        # 直接返回结构化的对话数据
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in refine_marketing_plan: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "conversation": []
        }), 500


@app.route("/inventory/analyze", methods=["POST"])
def analyze_inventory():
    try:
        data = request.json
        product = data.get("product")
        city = data.get("city", "全国")  # 添加城市参数，默认为"全国"
        
        if not product:
            return jsonify({"error": "缺少必要参数"}), 400
            
        # 使用AGI执行完整的库存分析策略，传入城市参数
        result = inventory_agi.execute_strategy(
            product=product,
            city=city
        )
        
        if not result:
            return jsonify({"error": "策略执行失败"}), 500
            
        # 确保返回结构化数据
        return jsonify({
            "factors": {
                "weather_impact": result.get("weather_impact", {}),
                "social_trends": result.get("social_trends", {}),
                "seasonal_events": result.get("seasonal_events", [])
            },
            "strategy": result.get("strategy", {}),
            "logistics": result.get("logistics", {}),
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in analyze_inventory: {str(e)}")
        return jsonify({
            "error": "分析库存时出现错误",
            "factors": {
                "weather_impact": {},
                "social_trends": {},
                "seasonal_events": []
            },
            "strategy": {},
            "logistics": {}
        }), 200  # 返回200以确保前端能处理错误


# 添加全局错误处理
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"应用错误: {str(error)}", exc_info=True)
    return jsonify({
        "error": "服务器内部错误",
        "message": str(error)
    }), 500

# 添加路由前的预处理
@app.before_request
def before_request():
    # 检查API密钥(如果需要)
    if request.path.startswith('/api/'):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "缺少API密钥"}), 401


# 判断是否是主程序运行，并设置Flask应用的host和debug模式
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",  # 修改为本地主机
        port=5000,         # 指定端口
        debug=True
    )
