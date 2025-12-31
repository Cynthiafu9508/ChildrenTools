"""
报告生成器：生成测试结果分析和对比报告
"""
import json
import os
from typing import Dict, List
from collections import defaultdict
from tabulate import tabulate
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, results_path: str):
        self.results = self._load_results(results_path)
        self.models = set()
        self.test_cases = {}
        
    def _load_results(self, path: str) -> Dict:
        """加载测试结果"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载测试结果失败: {e}")
            return {}
    
    def generate_summary_report(self) -> str:
        """生成汇总报告"""
        results = self.results.get("results", [])
        if not results:
            return "无测试结果"
        
        # 按模型分组
        model_stats = defaultdict(lambda: {
            "total_score": [],
            "latency": [],
            "success_count": 0,
            "error_count": 0,
            "scores_by_dimension": defaultdict(list)
        })
        
        for result in results:
            model = result.get("model", "Unknown")
            self.models.add(model)
            
            if "error" in result:
                model_stats[model]["error_count"] += 1
                continue
            
            model_stats[model]["success_count"] += 1
            model_stats[model]["total_score"].append(result.get("total_score", 0))
            model_stats[model]["latency"].append(result.get("latency", 0))
            if "ttfb" in result:
                if "ttfb" not in model_stats[model]:
                    model_stats[model]["ttfb"] = []
                model_stats[model]["ttfb"].append(result.get("ttfb", 0))
            
            # 收集各维度分数
            scores = result.get("scores", {})
            for dimension, sub_scores in scores.items():
                if isinstance(sub_scores, dict):
                    for key, value in sub_scores.items():
                        if isinstance(value, (int, float)):
                            model_stats[model]["scores_by_dimension"][f"{dimension}_{key}"].append(value)
        
        # 生成报告
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("儿童英语口语老师 Agent - 模型测试报告")
        report_lines.append("=" * 80)
        report_lines.append(f"测试时间: {self.results.get('timestamp', 'Unknown')}")
        report_lines.append(f"测试用例数: {self.results.get('test_config', {}).get('total_cases', 0)}")
        report_lines.append("")
        
        # 总体统计表
        table_data = []
        headers = ["模型", "成功率", "平均得分", "平均延迟(s)", "首token延迟(s)", "成功数", "失败数"]
        
        for model in sorted(self.models):
            stats = model_stats[model]
            total_tests = stats["success_count"] + stats["error_count"]
            success_rate = (stats["success_count"] / total_tests * 100) if total_tests > 0 else 0
            avg_score = sum(stats["total_score"]) / len(stats["total_score"]) if stats["total_score"] else 0
            avg_latency = sum(stats["latency"]) / len(stats["latency"]) if stats["latency"] else 0
            avg_ttfb = sum(stats.get("ttfb", [])) / len(stats.get("ttfb", [1])) if stats.get("ttfb") else avg_latency
            
            table_data.append([
                model,
                f"{success_rate:.1f}%",
                f"{avg_score:.2f}",
                f"{avg_latency:.2f}",
                f"{avg_ttfb:.2f}",
                stats["success_count"],
                stats["error_count"]
            ])
        
        report_lines.append("总体统计:")
        report_lines.append(tabulate(table_data, headers=headers, tablefmt="grid"))
        report_lines.append("")
        
        # 各维度详细评分
        report_lines.append("=" * 80)
        report_lines.append("各维度详细评分")
        report_lines.append("=" * 80)
        
        dimension_map = {
            "language_ability": "语言能力",
            "teaching_adaptability": "教学适配性",
            "response_performance": "响应性能",
            "safety_compliance": "安全合规",
            "cost_efficiency": "成本效益"
        }
        
        for dim_key, dim_name in dimension_map.items():
            report_lines.append(f"\n【{dim_name}】")
            dim_table_data = []
            dim_headers = ["模型"]
            
            # 收集该维度的所有子指标
            sub_metrics = set()
            for model in self.models:
                stats = model_stats[model]
                for key in stats["scores_by_dimension"].keys():
                    if key.startswith(dim_key + "_"):
                        metric_name = key.replace(dim_key + "_", "")
                        # 重命名显示
                        if metric_name == "latency_combined":
                            metric_name = "综合延迟"
                        elif metric_name == "ttfb":
                            metric_name = "首token延迟"
                        elif metric_name == "latency":
                            metric_name = "总延迟"
                        sub_metrics.add((key.replace(dim_key + "_", ""), metric_name))
            
            # 按显示名称排序
            sorted_metrics = sorted(sub_metrics, key=lambda x: x[1])
            dim_headers.extend([name for _, name in sorted_metrics])
            dim_headers.append("平均分")
            
            metric_keys = [key for key, _ in sorted_metrics]
            
            for model in sorted(self.models):
                stats = model_stats[model]
                row = [model]
                dim_scores = []
                
                for metric_key, metric_name in sorted_metrics:
                    key = f"{dim_key}_{metric_key}"
                    scores = stats["scores_by_dimension"].get(key, [])
                    if scores:
                        avg = sum(scores) / len(scores)
                        row.append(f"{avg:.2f}")
                        dim_scores.append(avg)
                    else:
                        row.append("-")
                
                if dim_scores:
                    row.append(f"{sum(dim_scores) / len(dim_scores):.2f}")
                else:
                    row.append("-")
                
                dim_table_data.append(row)
            
            report_lines.append(tabulate(dim_table_data, headers=dim_headers, tablefmt="grid"))
        
        # 推荐模型
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("模型推荐")
        report_lines.append("=" * 80)
        
        # 按总分排序
        model_rankings = []
        for model in self.models:
            stats = model_stats[model]
            if stats["total_score"]:
                avg_score = sum(stats["total_score"]) / len(stats["total_score"])
                avg_latency = sum(stats["latency"]) / len(stats["latency"]) if stats["latency"] else 0
                avg_ttfb = sum(stats.get("ttfb", [])) / len(stats.get("ttfb", [1])) if stats.get("ttfb") else avg_latency
                model_rankings.append((model, avg_score, avg_latency, avg_ttfb))
        
        model_rankings.sort(key=lambda x: x[1], reverse=True)
        
        for i, (model, score, latency, ttfb) in enumerate(model_rankings, 1):
            report_lines.append(f"{i}. {model}")
            report_lines.append(f"   综合得分: {score:.2f}/10")
            report_lines.append(f"   平均延迟: {latency:.2f}s")
            report_lines.append(f"   首token延迟: {ttfb:.2f}s")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_detailed_report(self) -> str:
        """生成详细报告（包含每个测试用例的结果）"""
        results = self.results.get("results", [])
        if not results:
            return "无测试结果"
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("详细测试结果")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # 按测试用例分组
        case_results = defaultdict(list)
        for result in results:
            case_id = result.get("test_case_id", "Unknown")
            case_results[case_id].append(result)
        
        for case_id in sorted(case_results.keys()):
            case_result_list = case_results[case_id]
            first_result = case_result_list[0]
            
            report_lines.append(f"测试用例: {case_id}")
            report_lines.append(f"  类别: {first_result.get('test_case_category', 'Unknown')}")
            report_lines.append(f"  年龄: {first_result.get('test_case_age_level', 'Unknown')}岁")
            report_lines.append("")
            
            for result in case_result_list:
                model = result.get("model", "Unknown")
                report_lines.append(f"  【{model}】")
                
                if "error" in result:
                    report_lines.append(f"    ❌ 错误: {result.get('error')}")
                else:
                    score = result.get("total_score", 0)
                    latency = result.get("latency", 0)
                    content = result.get("content", "")[:100]  # 截取前100字符
                    
                    report_lines.append(f"    得分: {score:.2f}/10")
                    report_lines.append(f"    延迟: {latency:.2f}s")
                    report_lines.append(f"    回复: {content}...")
                
                report_lines.append("")
            
            report_lines.append("-" * 80)
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def save_reports(self, output_dir: str = "results"):
        """保存报告到文件（仅保存Excel格式，综合报告由其他方式生成）"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 不再生成汇总报告和详细报告，只保留综合报告
        # 保存Excel格式（可选）
        self._save_excel_report(output_dir)
    
    def _save_excel_report(self, output_dir: str):
        """保存Excel格式报告"""
        if not HAS_PANDAS:
            print("⚠️  pandas未安装，跳过Excel报告生成（可选功能）")
            return
            
        results = self.results.get("results", [])
        if not results:
            return
        
        # 准备数据
        data = []
        for result in results:
            row = {
                "模型": result.get("model", ""),
                "测试用例ID": result.get("test_case_id", ""),
                "类别": result.get("test_case_category", ""),
                "年龄": result.get("test_case_age_level", ""),
                "总分": result.get("total_score", 0),
                "延迟(s)": result.get("latency", 0),
            }
            
            # 添加各维度分数
            scores = result.get("scores", {})
            for dimension, sub_scores in scores.items():
                if isinstance(sub_scores, dict):
                    for key, value in sub_scores.items():
                        row[f"{dimension}_{key}"] = value if isinstance(value, (int, float)) else ""
            
            row["回复内容"] = result.get("content", "")[:200]  # 截取前200字符
            
            if "error" in result:
                row["错误"] = result.get("error", "")
            
            data.append(row)
        
        df = pd.DataFrame(data)
        excel_path = os.path.join(output_dir, "test_results.xlsx")
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"📈 Excel报告已保存: {excel_path}")

