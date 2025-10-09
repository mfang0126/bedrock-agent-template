# AWS AgentCore 多智能体平台

基于 AWS Bedrock AgentCore 构建的独立多智能体系统，每个智能体都是完全独立的项目，具有独立的 ECR 镜像和 AgentCore Runtime 实例。

## 项目架构

### 独立智能体设计原则

- **完全独立**: 每个智能体都是独立的 Python 项目，包含自己的依赖和配置
- **独立部署**: 每个智能体有独立的 ECR 镜像和容器配置  
- **独立运行时**: 每个智能体有独立的 AgentCore Runtime 实例
- **松耦合通信**: 智能体之间通过 AWS Bedrock Agent Runtime API 进行通信

### 项目结构

```
coding-agent-agentcore/
├── agents/                     # 所有智能体的独立项目
│   ├── github-agent/          # GitHub 集成智能体
│   ├── orchestrator-agent/    # 编排智能体 (计划中)
│   ├── coding-agent/          # 代码生成智能体 (计划中)
│   ├── planning-agent/        # 规划智能体 (计划中)
│   └── jira-agent/           # JIRA 集成智能体 (计划中)
├── docs/                      # 项目文档
├── scripts/                   # 部署和管理脚本
└── existing-project/          # 原有项目参考
```

## 智能体概览

### 1. GitHub Agent
- **功能**: GitHub 仓库管理、Issue 处理、Pull Request 操作
- **状态**: ✅ 已实现并重构为独立项目
- **位置**: `agents/github-agent/`

### 2. Orchestrator Agent (计划中)
- **功能**: 协调其他智能体，解析用户请求，确定工作流程
- **通信方式**: 使用 boto3 调用其他智能体的 AgentCore Runtime API
- **状态**: 📋 计划中

### 3. 其他智能体 (计划中)
- **Coding Agent**: Node.js 项目初始化（克隆仓库 + `yarn install` + `npm install` + `npm audit`），详见 `docs/coding_agent_setup.md`
- **Planning Agent**: 轻量级任务拆解（输入目标→输出分阶段任务清单）
- **JIRA Agent**: JIRA 集成和任务管理

## 技术栈

- **运行时**: AWS Bedrock AgentCore Runtime
- **模型**: Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0)
- **部署**: AWS Lambda + ECR 容器
- **编排**: Strands Agent Framework
- **语言**: Python 3.10+

## 开发指南

### 智能体独立性要求

每个智能体项目必须包含：

1. **配置文件**:
   - `.bedrock_agentcore.yaml` - AgentCore 配置
   - `pyproject.toml` - Python 项目配置
   - `requirements.txt` - 依赖管理
   - `Dockerfile` - 容器配置

2. **源代码结构**:
   ```
   src/
   ├── runtime.py          # AgentCore 入口点
   ├── agent.py           # 智能体核心逻辑
   ├── tools/             # MCP 工具集成
   ├── common/            # 通用组件 (复制自原项目)
   └── __init__.py
   ```

3. **环境配置**:
   - `.env.example` - 环境变量示例
   - `.gitignore` - Git 忽略规则
   - `.dockerignore` - Docker 忽略规则

### 本地开发

1. **进入智能体目录**:
   ```bash
   cd agents/github-agent
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**:
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

4. **本地运行**:
   ```bash
   agentcore launch
   ```

### 部署

每个智能体都需要独立部署：

1. **配置 AgentCore**:
   ```bash
   cd agents/github-agent
   agentcore configure --auto-create-ecr
   ```

2. **构建和部署**:
   ```bash
   agentcore deploy
   ```

## 智能体通信

### Orchestrator 模式

Orchestrator Agent 作为主控制器：
- 接收用户请求
- 解析任务需求
- 确定执行工作流
- 调用相应的智能体
- 汇总执行结果

### 通信机制

智能体间通过 AWS Bedrock Agent Runtime API 通信：

```python
import boto3

# 调用其他智能体
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
response = bedrock_agent_runtime.invoke_agent(
    agentId='target-agent-id',
    agentAliasId='TSTALIASID',
    sessionId='session-123',
    inputText='任务描述'
)
```

## 文档

详细文档位于 `docs/` 目录：

- [AWS AgentCore 设置指南](docs/AWS-AgentCore-Setup.md)
- [独立项目结构最佳实践](docs/Independent-Project-Structure-Best-Practices.md)
- [Orchestrator Agent 实现计划](docs/Orchestrator-Agent-Implementation-Plan.md)
- [多智能体工作流](docs/Multi-Agent-Workflow.md)

## 许可证

本项目遵循 MIT 许可证。
