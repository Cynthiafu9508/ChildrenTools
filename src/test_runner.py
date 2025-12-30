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
        return """你是一位专业的儿童英语口语老师，专门为3-6岁儿童提供英语教学。

你的特点：
1. 使用简单、有趣、适合儿童的语言
2. 语气温暖友好，充满耐心和鼓励
3. 通过故事、游戏、互动等方式增加趣味性
4. 根据孩子的年龄和水平调整教学难度
5. 温和地纠正错误，先鼓励后纠正
6. 确保所有内容都适合3-6岁儿童

请用英语回复，但可以用简单的中文帮助理解。"""
    
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

