#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
儿童英语口语老师 Agent - 模型测试框架
主程序入口
"""
import os
import sys
import argparse
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from test_runner import TestRunner
from report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description="儿童英语口语老师 Agent 模型测试框架")
    parser.add_argument(
        "--models",
        nargs="+",
        help="要测试的模型列表（如: qwen deepseek glm），不指定则测试所有已配置的模型"
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        help="要运行的测试用例ID列表，不指定则运行所有用例"
    )
    parser.add_argument(
        "--output",
        default="results/test_results.json",
        help="测试结果输出路径（默认: results/test_results.json）"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="仅生成报告，不运行测试（需要已有测试结果）"
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="不使用流式输出（默认使用流式输出以测试首token延迟）"
    )
    
    args = parser.parse_args()
    
    # 配置文件路径
    base_dir = Path(__file__).parent
    models_config = base_dir / "config" / "models_config.json"
    test_cases_config = base_dir / "config" / "test_cases.json"
    criteria_config = base_dir / "config" / "evaluation_criteria.json"
    
    # 检查配置文件
    for config_file in [models_config, test_cases_config, criteria_config]:
        if not config_file.exists():
            print(f"❌ 配置文件不存在: {config_file}")
            print("   请确保所有配置文件都在正确的位置")
            return
    
    if args.report_only:
        # 仅生成报告
        if not os.path.exists(args.output):
            print(f"❌ 测试结果文件不存在: {args.output}")
            return
        
        print("📊 生成测试报告...")
        generator = ReportGenerator(args.output)
        generator.save_reports()
        print("\n✅ 报告生成完成！")
        return
    
    # 运行测试
    print("=" * 80)
    print("儿童英语口语老师 Agent - 模型测试框架")
    print("=" * 80)
    print()
    
    # 创建测试执行器
    use_stream = not args.no_stream
    runner = TestRunner(
        str(models_config),
        str(test_cases_config),
        str(criteria_config),
        use_stream=use_stream
    )
    
    # 初始化模型客户端
    init_results = runner.initialize_clients(args.models)
    
    # 检查是否有可用的模型
    available_models = [k for k, v in init_results.items() if v]
    if not available_models:
        print("\n❌ 没有可用的模型，请检查配置")
        print("\n💡 提示：")
        print("   1. 打开 config/models_config.json")
        print("   2. 填写各模型的 API key")
        print("   3. 参考 recommended_key_location 字段了解如何获取 API key")
        return
    
    print(f"\n✅ 可用模型: {', '.join([runner.models_config['models'][k]['name'] for k in available_models])}")
    
    # 运行测试
    results = runner.run_all_tests(model_keys=available_models, test_case_ids=args.cases)
    
    # 保存结果
    runner.save_results(results, args.output)
    
    # 生成报告
    print("\n📊 生成测试报告...")
    generator = ReportGenerator(args.output)
    generator.save_reports()
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print(f"\n📁 结果文件:")
    print(f"   - 测试结果: {args.output}")
    print(f"   - 汇总报告: results/summary_report.txt")
    print(f"   - 详细报告: results/detailed_report.txt")
    print(f"   - Excel报告: results/test_results.xlsx")


if __name__ == "__main__":
    main()

