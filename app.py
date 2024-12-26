from flask import Flask, render_template, request, jsonify
from findbigV import find_bigV
import json

# 实例化Flask应用
app = Flask(__name__)


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


# 判断是否是主程序运行，并设置Flask应用的host和debug模式
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
