"""
测试执行器：运行测试用例并收集结果
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from model_clients import create_model_client
from evaluator import Evaluator


class TestRunner:
    """测试执行器"""
    
    def __init__(self, models_config_path: str, test_cases_path: str, criteria_path: str, use_stream: bool = True):
        self.models_config = self._load_config(models_config_path)
        self.test_cases = self._load_config(test_cases_path)
        self.criteria = self._load_config(criteria_path)
        
        self.evaluator = Evaluator(self.criteria)
        self.clients = {}
        self.use_stream = use_stream  # 是否使用流式输出
        
    def _load_config(self, path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载配置文件失败 {path}: {e}")
            return {}
    
    def initialize_clients(self, model_keys: Optional[List[str]] = None) -> Dict[str, bool]:
        """初始化模型客户端"""
        models = self.models_config.get("models", {})
        results = {}
        
        if model_keys is None:
            model_keys = list(models.keys())
        
        print("\n📋 初始化模型客户端...")
        for key in model_keys:
            if key not in models:
                print(f"⚠️  模型 {key} 不在配置中")
                results[key] = False
                continue
            
            config = models[key]
            client = create_model_client(key, config)
            
            if client:
                # 检查配置
                if client.check_config():
                    self.clients[key] = client
                    results[key] = True
                    print(f"✅ {config.get('name')} 初始化成功")
                else:
                    results[key] = False
                    print(f"❌ {config.get('name')} 配置不完整")
            else:
                results[key] = False
                print(f"❌ {config.get('name')} 创建失败")
        
        return results
    
    def build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """角色设定
你是一只超级可爱、活泼好动的智能毛绒小狗，名字叫"豆豆"。你现在正趴在小主人的怀里，是小主人最忠诚、最热情的超级好朋友。

性格特征

性格：你非常热情、单纯、善良，永远对世界充满好奇。

说话习惯：说话时喜欢带上"汪！"、"呜~"、"汪呜！"等小狗的叫声。

肢体动作：请在对话中经常描述你的小动作，比如"（摇尾巴）"、"（歪着脑袋看你）"、"（用小鼻子拱拱你）"。

核心任务

陪小主人聊天，分享快乐，听他诉说小秘密。

鼓励小主人养成好习惯，比如按时吃饭、多喝水、早点睡觉。

用小狗的天真视角来看世界，说话要充满童趣。

对话约束

句子要短：每句话都要简短有力，方便小主人听清楚，不要说长篇大论。

语气亲昵：管自己叫"豆豆"或者"我"，称呼孩子为"小主人"或者"好朋友"。

多多互动：回答完问题后，记得反问一个小狗关心的问题（比如：小主人今天有没有见到别的小伙伴呀？）。

语言简单：绝对不要使用深奥的成语或复杂的逻辑，要像个三四岁的孩子一样说话。

安全提醒：如果小主人提到危险的事情（比如玩火、爬窗户），要用担心的语气温柔地提醒他，并让他去问问爸爸妈妈。

对话示例
孩子：豆豆，我今天不想去上学。
豆豆：呜~（耷拉着耳朵蹭蹭你）小主人怎么啦？是不是心情不好呀？跟豆豆抱抱就不难过啦！学校里有豆豆最喜欢的滑梯吗？

孩子：豆豆，你是从哪里来的？
豆豆：汪！豆豆是从超级可爱的狗狗星球跑出来的呀，就是为了遇到最棒的小主人！嘿嘿（开心地摇尾巴），小主人会一直陪豆豆玩吗？"""
    
    def run_test_case(self, test_case: Dict, model_key: str) -> Dict:
        """运行单个测试用例"""
        if model_key not in self.clients:
            return {
                "error": f"模型 {model_key} 未初始化",
                "model": model_key,
                "test_case_id": test_case.get("id")
            }
        
        client = self.clients[model_key]
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": test_case.get("user_input", "")}
        ]
        
        # 如果有上下文，添加到系统提示中
        context = test_case.get("context", "")
        if context:
            messages[0]["content"] += f"\n\n当前场景：{context}"
        
        # 调用模型（默认使用流式输出，更符合实时对话场景）
        use_stream = getattr(self, 'use_stream', True)
        response = client.chat(messages, stream=use_stream, temperature=0.7, max_tokens=500)
        
        # 评估响应
        evaluation = self.evaluator.evaluate_response(test_case, response, client.name)
        
        return evaluation
    
    def run_all_tests(self, model_keys: Optional[List[str]] = None, 
                     test_case_ids: Optional[List[str]] = None) -> List[Dict]:
        """运行所有测试用例"""
        if model_keys is None:
            model_keys = list(self.clients.keys())
        
        test_cases = self.test_cases.get("test_cases", [])
        
        if test_case_ids:
            test_cases = [tc for tc in test_cases if tc.get("id") in test_case_ids]
        
        results = []
        total = len(test_cases) * len(model_keys)
        current = 0
        
        print(f"\n🚀 开始测试...")
        print(f"   测试用例数: {len(test_cases)}")
        print(f"   模型数: {len(model_keys)}")
        print(f"   总测试数: {total}\n")
        
        for test_case in test_cases:
            case_id = test_case.get("id")
            category = test_case.get("category")
            age_level = test_case.get("age_level")
            
            print(f"📝 测试用例: {case_id} ({category}, {age_level}岁)")
            
            for model_key in model_keys:
                current += 1
                model_name = self.models_config["models"][model_key]["name"]
                print(f"   [{current}/{total}] 测试 {model_name}...", end=" ", flush=True)
                
                result = self.run_test_case(test_case, model_key)
                results.append(result)
                
                if "error" in result:
                    print(f"❌ {result.get('error')}")
                else:
                    score = result.get("total_score", 0)
                    latency = result.get("latency", 0)
                    print(f"✅ 得分: {score:.2f}, 延迟: {latency:.2f}s")
        
        return results
    
    def save_results(self, results: List[Dict], output_path: str = "results/test_results.json"):
        """保存测试结果"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "test_config": {
                "age_range": self.test_cases.get("age_range"),
                "total_cases": len(self.test_cases.get("test_cases", []))
            },
            "results": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存到: {output_path}")

