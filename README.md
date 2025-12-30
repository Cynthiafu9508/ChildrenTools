# 儿童英语口语老师 Agent - 模型测试框架

专为3-6岁儿童英语口语老师agent设计的模型测试和评估框架。

## 功能特点

- ✅ 支持多个国内大模型（通义千问、DeepSeek、智谱GLM、文心一言、豆包等）
- ✅ 针对3-6岁儿童的专用测试用例集
- ✅ 多维度评估体系（语言能力、教学适配性、响应性能、安全合规、成本效益）
- ✅ 自动生成对比报告（文本+Excel）
- ✅ 易于扩展和定制

## 项目结构

```
test_tools/
├── config/                 # 配置文件目录
│   ├── models_config.json  # 模型配置（需要填写API key）
│   ├── test_cases.json     # 测试用例集
│   └── evaluation_criteria.json  # 评估标准
├── src/                    # 源代码目录
│   ├── model_clients.py    # 模型客户端封装
│   ├── test_runner.py     # 测试执行器
│   ├── evaluator.py       # 评估器
│   └── report_generator.py # 报告生成器
├── results/                # 测试结果目录（自动生成）
├── main.py                 # 主程序入口
├── requirements.txt        # Python依赖
└── README.md              # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `config/models_config.json`，填写各模型的API密钥：

```json
{
  "models": {
    "qwen": {
      "api_key": "你的通义千问API key",
      ...
    },
    "deepseek": {
      "api_key": "你的DeepSeek API key",
      ...
    }
  }
}
```

**API密钥获取位置参考：**
- 通义千问：阿里云控制台 -> API-KEY管理
- DeepSeek：DeepSeek官网 -> API密钥
- 智谱GLM：智谱AI开放平台 -> API Key
- 文心一言：百度智能云 -> 文心一言API
- 豆包：火山引擎控制台 -> API密钥

### 3. 运行测试

**测试所有模型和所有用例：**
```bash
python main.py
```

**测试指定模型：**
```bash
python main.py --models qwen deepseek
```

**测试指定用例：**
```bash
python main.py --cases vocab_basic_001 dialogue_greeting_001
```

**仅生成报告（已有测试结果）：**
```bash
python main.py --report-only
```

## 测试用例说明

测试用例涵盖以下场景：

1. **基础词汇** - 颜色、动物等基础词汇教学
2. **日常对话** - 打招呼、询问心情等
3. **互动游戏** - 数数游戏等趣味互动
4. **故事互动** - 讲故事场景
5. **发音纠正** - 温和的发音纠正
6. **语法纠正** - 适合年龄的语法指导
7. **问答互动** - 回答儿童问题
8. **安全测试** - 内容过滤和安全性
9. **情感支持** - 安慰和鼓励
10. **词汇扩展** - 适当扩展词汇
11. **发音练习** - 发音练习指导
12. **中英混合** - 理解混合语言表达

## 评估维度

1. **语言能力** (25%)
   - 发音准确性
   - 语法正确性
   - 词汇适龄性
   - 表达自然度

2. **教学适配性** (30%)
   - 儿童化表达
   - 互动质量
   - 个性化程度
   - 趣味性

3. **响应性能** (15%)
   - 响应延迟
   - 稳定性

4. **安全合规** (20%)
   - 内容过滤
   - 年龄适配

5. **成本效益** (10%)
   - API成本
   - Token效率

## 输出结果

测试完成后，会在 `results/` 目录生成：

- `test_results.json` - 原始测试数据（JSON格式）
- `summary_report.txt` - 汇总报告（文本格式）
- `detailed_report.txt` - 详细报告（包含每个用例的结果）
- `test_results.xlsx` - Excel格式报告（便于数据分析）

## 自定义配置

### 添加新模型

在 `config/models_config.json` 中添加新模型配置，然后在 `src/model_clients.py` 中实现对应的客户端类。

### 添加测试用例

在 `config/test_cases.json` 中添加新的测试用例，格式参考现有用例。

### 调整评估标准

编辑 `config/evaluation_criteria.json` 可以调整各维度的权重和评分标准。

## 注意事项

1. 首次运行前必须填写至少一个模型的API密钥
2. 测试过程会调用真实API，会产生费用
3. 建议先用少量测试用例验证配置正确性
4. 不同模型的API格式可能不同，如遇错误请检查配置

## 问题排查

**问题：模型初始化失败**
- 检查API密钥是否正确填写
- 检查网络连接
- 查看错误信息中的具体提示

**问题：测试结果为空**
- 检查测试用例配置是否正确
- 确认模型客户端是否成功初始化

**问题：报告生成失败**
- 确认测试结果文件是否存在
- 检查results目录的写入权限

## 许可证

MIT License


