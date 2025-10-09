# AWS AgentCore 独立项目结构最佳实践

## 概述

基于AWS AgentCore的架构要求，每个agent需要独立的ECR镜像和AgentCore Runtime实例。本文档提供了构建独立agent项目的最佳实践指南。

## 核心原则

### 1. 独立部署原则
- 每个agent都是完全独立的Python项目
- 每个agent有独立的ECR镜像和容器配置
- 每个agent有独立的AgentCore Runtime实例
- 共享组件通过Python包的方式进行复用

### 2. ECR镜像管理
- 每个agent需要独立的ECR仓库和镜像
- 即使多个agent共享相同的runtime代码，也需要独立的镜像
- 通过 `agentcore configure --auto-create-ecr` 自动创建ECR仓库
- 每个agent的 `containerUri` 指向不同的ECR镜像

## 推荐的项目结构

### 顶层目录结构
```
multi-agent-project/
├── agents/                      # 所有agent的独立项目
│   ├── coding-agent/           # Coding Agent独立项目
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   └── .bedrock_agentcore.yaml
│   ├── plan-agent/             # Plan Agent独立项目
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   └── .bedrock_agentcore.yaml
│   └── orchestrator-agent/     # Orchestrator Agent独立项目
│       ├── src/
│       ├── pyproject.toml
│       ├── requirements.txt
│       └── .bedrock_agentcore.yaml
├── shared/                     # 共享组件包
│   ├── pyproject.toml          # 共享包配置
│   ├── src/
│   │   └── shared_components/
│   │       ├── __init__.py
│   │       ├── utils/          # 通用工具
│   │       ├── schemas/        # 数据模型
│   │       └── mcp_tools/      # MCP工具集成
│   └── README.md
├── docs/                       # 项目文档
├── scripts/                    # 部署和管理脚本
└── README.md                   # 项目总览
```

## 共享组件的使用方式

### 1. 将 shared 打包为 Python 包

在 `shared/pyproject.toml` 中配置：

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "shared-components"
version = "0.1.0"
description = "Shared components for multi-agent project"
dependencies = [
    "pydantic>=2.0.0",
    "boto3>=1.34.0",
    # 其他共享依赖
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "isort>=5.0.0",
]
```

### 2. 在各个 agent 中引用共享组件

#### 方式一：开发模式安装（推荐）

在每个 agent 的 `requirements.txt` 中添加：
```txt
# 本地开发模式安装共享组件
-e ../../shared

# 其他依赖
boto3>=1.34.0
# ...
```

或在 `pyproject.toml` 中：
```toml
[project]
dependencies = [
    "shared-components @ file://../../shared",
    "boto3>=1.34.0",
    # 其他依赖
]
```

#### 方式二：私有 PyPI 仓库

1. 将 shared 包发布到私有 PyPI 仓库
2. 在各个 agent 中正常安装：
```txt
shared-components==0.1.0
```

### 3. 使用共享组件

在 agent 代码中导入：

```python
# coding-agent/src/main.py
from shared_components.utils.logger import setup_logger
from shared_components.schemas.task import TaskSchema
from shared_components.mcp_tools.git_tools import GitTools

def main():
    logger = setup_logger("coding-agent")
    task = TaskSchema(...)
    git_tools = GitTools()
    # ...
```

### 单个智能体项目结构
```
agents/coding-agent/
├── src/
│   ├── __init__.py
│   ├── main.py              # 入口点文件 (entrypoint)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py          # 核心逻辑
│   │   └── handlers.py      # 处理器
│   ├── tools/               # MCP工具
│   │   ├── __init__.py
│   │   └── code_tools.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   └── test_tools.py
├── .bedrock_agentcore.yaml  # AgentCore配置
├── pyproject.toml           # Python项目配置
├── requirements.txt         # 依赖列表
├── Dockerfile              # 容器配置
├── .dockerignore           # Docker忽略文件
├── .gitignore              # Git忽略文件
├── .env.example            # 环境变量示例
├── README.md               # 智能体说明
└── venv/                   # 虚拟环境 (本地开发)
```

## 配置文件模板

### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "coding-agent"
version = "0.1.0"
description = "AWS AgentCore Coding Agent"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "boto3>=1.34.0",
    "agentcore>=0.1.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
]

[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### requirements.txt
```txt
# Core dependencies
boto3>=1.34.0
agentcore>=0.1.0
pydantic>=2.0.0
python-dotenv>=1.0.0

# AWS SDK extensions
aws-lambda-powertools>=2.0.0

# Development dependencies (optional)
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0
mypy>=1.0.0
```

### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env
.env.local
.env.production

# AWS
.aws/
*.pem

# AgentCore
.bedrock_agentcore.yaml.bak

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# MyPy
.mypy_cache/
.dmypy.json
dmypy.json
```

### .dockerignore
```dockerignore
# Version control
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode
.idea
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Documentation
README.md
docs/
*.md

# Tests
tests/
test_*

# Development files
.env.example
requirements-dev.txt
```

### Dockerfile 模板
```dockerfile
FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies
RUN yum update -y && \
    yum install -y gcc && \
    yum clean all

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/src:${PYTHONPATH}"

# Install OpenTelemetry (AgentCore requirement)
RUN pip install aws-opentelemetry-distro

# Set the CMD to your handler
CMD ["opentelemetry-instrument", "--traces_exporter", "none", "--metrics_exporter", "none", "src.main.handler"]
```

### .env.example
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# AgentCore Configuration
AGENT_NAME=coding-agent
EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/AgentCoreExecutionRole
ECR_REPOSITORY=coding-agent-repo

# Application Configuration
LOG_LEVEL=INFO
DEBUG=false

# Model Configuration
MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
MAX_TOKENS=4096
TEMPERATURE=0.1
```

## 开发工作流

### 1. 初始化共享组件包

```bash
# 在项目根目录
cd shared
pip install -e .  # 开发模式安装
```

### 2. 初始化各个 agent 项目

```bash
# 为每个 agent 创建独立项目
cd agents/coding-agent
agentcore configure --entrypoint src/main.py --auto-create-role --auto-create-ecr

# 安装依赖（包括共享组件）
pip install -r requirements.txt

# 开发和测试
agentcore launch --local
```

### 3. 共享组件更新流程

当更新共享组件时：

```bash
# 在 shared 目录
cd shared
# 修改代码后，版本会自动更新（开发模式）
# 各个 agent 会自动使用最新的共享组件

# 如果使用私有 PyPI，需要重新发布
python -m build
twine upload dist/* --repository-url YOUR_PRIVATE_PYPI_URL
```

### 4. 独立部署各个 agent

```bash
# 每个 agent 独立部署
cd agents/coding-agent
agentcore launch  # 构建镜像并推送到独立的ECR仓库

cd ../plan-agent  
agentcore launch  # 构建另一个独立的镜像

cd ../orchestrator-agent
agentcore launch  # 构建第三个独立的镜像
```

## Docker Build Context 处理

### 问题说明
由于共享组件在 agent 项目的父目录中，Docker build 时会遇到 context 范围问题：

```
multi-agent-project/
├── agents/
│   └── coding-agent/           # Docker build context 在这里
│       ├── Dockerfile          # 无法直接访问 ../../shared
│       └── src/
└── shared/                     # 在 build context 外面
```

### 解决方案

#### 方案一：调整 Build Context（推荐）

在项目根目录执行构建，并调整 Dockerfile：

```bash
# 在项目根目录执行
cd multi-agent-project/
docker build -f agents/coding-agent/Dockerfile -t coding-agent .
```

相应的 Dockerfile：
```dockerfile
# agents/coding-agent/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 复制共享组件（相对于根目录）
COPY shared/ ./shared/

# 复制当前 agent（相对于根目录）
COPY agents/coding-agent/ ./

# 安装共享组件
RUN pip install -e ./shared

# 安装 agent 依赖
RUN pip install -r requirements.txt

CMD ["python", "src/main.py"]
```

#### 方案二：AgentCore 配置调整

修改 `.bedrock_agentcore.yaml` 配置：

```yaml
# agents/coding-agent/.bedrock_agentcore.yaml
agent_name: coding-agent
runtime: src/main.py
docker:
  build_context: ../../  # 指向项目根目录
  dockerfile: Dockerfile
```

#### 方案三：符号链接方式

在每个 agent 目录创建符号链接：

```bash
# 在 agent 目录中
cd agents/coding-agent/
ln -s ../../shared ./shared

# 添加到 .gitignore
echo "shared" >> .gitignore
```

然后 Dockerfile 可以正常引用：
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 现在可以直接复制符号链接指向的内容
COPY shared/ ./shared/
COPY src/ ./src/
COPY requirements.txt .

RUN pip install -e ./shared
RUN pip install -r requirements.txt

CMD ["python", "src/main.py"]
```

### 推荐的构建流程

```bash
# 1. 在项目根目录
cd multi-agent-project/

# 2. 为每个 agent 创建符号链接（一次性操作）
cd agents/coding-agent && ln -s ../../shared ./shared && cd ../..
cd agents/plan-agent && ln -s ../../shared ./shared && cd ../..

# 3. 正常使用 agentcore 命令
cd agents/coding-agent/
agentcore launch
```

### 1. 代码复用
- 共享组件统一管理，避免重复代码
- 通过 Python 包机制实现标准化的依赖管理
- 版本控制清晰，便于维护

### 2. 独立部署
- 每个 agent 有独立的 ECR 镜像和 Runtime
- 可以独立更新和部署，不影响其他 agent
- 符合 AWS AgentCore 的架构要求

### 3. 开发效率
- 开发模式安装（`-e`）支持实时代码更新
- 清晰的项目结构，便于团队协作
- 标准化的依赖管理和构建流程

### 4. 灵活性
- 可以选择本地开发模式或私有 PyPI 仓库
- 支持不同 agent 使用不同版本的共享组件
- 便于进行 A/B 测试和渐进式部署

## 重要注意事项

### 1. 避免配置冲突
- **绝对不要**在同一目录运行多次 `agentcore configure`
- 每个智能体使用独立的目录
- 备份重要的配置修改

### 2. Dockerfile 管理
```bash
# 备份自定义修改
cp Dockerfile Dockerfile.backup

# 如果需要重新配置，先恢复备份
cp Dockerfile.backup Dockerfile
```

### 3. 依赖管理
- 使用 `requirements.txt` 锁定版本
- 定期更新依赖并测试兼容性
- 使用虚拟环境隔离依赖

### 4. 环境变量管理
- 使用 `.env` 文件管理本地配置
- 生产环境使用 AWS Systems Manager Parameter Store
- 永远不要提交敏感信息到版本控制

### 5. 测试策略
- 单元测试覆盖核心逻辑
- 集成测试验证MCP工具
- 使用 `agentcore gateway` 进行本地测试

## 共享组件管理

### 创建共享库
```bash
# 在项目根目录
mkdir -p shared/common
touch shared/__init__.py
touch shared/common/__init__.py
```

### 在智能体中使用共享组件
```python
# 在智能体的 requirements.txt 中
-e ../../shared

# 在代码中导入
from shared.common.utils import helper_function
```

## 监控和日志

### 日志配置
```python
import logging
import os

# 配置日志
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### 性能监控
- 使用 AWS CloudWatch 监控指标
- 配置 X-Ray 追踪请求
- 设置告警和通知

这种独立的项目结构确保了每个智能体的完全隔离，避免了配置冲突，并提供了清晰的开发和部署工作流。