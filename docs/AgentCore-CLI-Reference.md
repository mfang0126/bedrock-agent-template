# AWS AgentCore CLI 命令参考

## 概述

AWS AgentCore 提供了两套主要的CLI工具：
1. **agentcore CLI** - 用于开发和部署智能体的工具包
2. **bedrock-agentcore-control CLI** - 用于管理AWS资源的控制平面工具

## agentcore CLI (开发工具包)

### 安装
```bash
pip install agentcore
```

### 主要命令

#### `agentcore configure`
配置新的智能体项目

```bash
agentcore configure [OPTIONS]
```

**选项：**
- `-e, --entrypoint TEXT` - 指定入口点文件
- `-n, --name TEXT` - 智能体名称
- `--execution-role TEXT` - 执行角色ARN
- `--auto-create-role` - 自动创建执行角色
- `--ecr-repository TEXT` - ECR仓库名称
- `--auto-create-ecr` - 自动创建ECR仓库

**生成的文件：**
- `.bedrock_agentcore.yaml` - 配置文件
- `Dockerfile` - 容器镜像定义

#### `agentcore launch`
构建并部署智能体

```bash
agentcore launch [OPTIONS]
```

**选项：**
- `--config-file TEXT` - 配置文件路径
- `--build-only` - 仅构建不部署

#### `agentcore invoke`
调用已部署的智能体

```bash
agentcore invoke [OPTIONS]
```

#### `agentcore status`
查看智能体状态

```bash
agentcore status [OPTIONS]
```

#### `agentcore gateway`
启动本地网关进行测试

```bash
agentcore gateway [OPTIONS]
```

## bedrock-agentcore-control CLI (控制平面)

### 安装
```bash
pip install awscli
aws configure  # 配置AWS凭证
```

### 主要命令

#### Agent Runtime 管理

##### `create-agent-runtime`
创建智能体运行时

```bash
aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name "my-agent" \
    --agent-runtime-artifact "s3://bucket/artifact.zip" \
    --role-arn "arn:aws:iam::account:role/role-name" \
    --network-configuration '{
        "vpcConfiguration": {
            "subnetIds": ["subnet-xxx"],
            "securityGroupIds": ["sg-xxx"]
        }
    }'
```

##### `list-agent-runtimes`
列出所有智能体运行时

```bash
aws bedrock-agentcore-control list-agent-runtimes
```

##### `get-agent-runtime`
获取智能体运行时详情

```bash
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-name "my-agent"
```

##### `update-agent-runtime`
更新智能体运行时

```bash
aws bedrock-agentcore-control update-agent-runtime \
    --agent-runtime-name "my-agent" \
    --agent-runtime-artifact "s3://bucket/new-artifact.zip"
```

##### `delete-agent-runtime`
删除智能体运行时

```bash
aws bedrock-agentcore-control delete-agent-runtime \
    --agent-runtime-name "my-agent"
```

#### Agent Runtime Endpoint 管理

##### `create-agent-runtime-endpoint`
创建智能体运行时端点

```bash
aws bedrock-agentcore-control create-agent-runtime-endpoint \
    --agent-runtime-endpoint-name "my-endpoint" \
    --agent-runtime-name "my-agent"
```

##### `delete-agent-runtime-endpoint`
删除智能体运行时端点

```bash
aws bedrock-agentcore-control delete-agent-runtime-endpoint \
    --agent-runtime-endpoint-name "my-endpoint"
```

## bedrock-agentcore CLI (数据平面)

### 主要命令

#### 批处理操作
```bash
aws bedrock-agentcore batch-invoke-agent
aws bedrock-agentcore batch-get-agent-memory
```

#### 事件管理
```bash
aws bedrock-agentcore create-agent-memory
aws bedrock-agentcore delete-agent-memory
aws bedrock-agentcore get-agent-memory
```

#### 会话控制
```bash
aws bedrock-agentcore invoke-agent
aws bedrock-agentcore retrieve-and-generate
```

## 最佳实践

### 1. 多智能体项目结构
- 每个智能体使用独立的项目目录
- 避免在同一目录多次运行 `agentcore configure`
- 使用版本控制管理配置文件

### 2. Dockerfile 管理
- 备份自定义的 Dockerfile 修改
- 注意 `agentcore configure` 会覆盖现有 Dockerfile
- 考虑使用 `.dockerignore` 优化构建

### 3. 资源管理
- 使用 `bedrock-agentcore-control` 进行生产环境管理
- 定期清理未使用的运行时和端点
- 监控资源使用情况和成本

### 4. 开发工作流
```bash
# 1. 初始化项目
agentcore configure -e main.py -n my-agent --auto-create-role --auto-create-ecr

# 2. 开发和测试
agentcore gateway  # 本地测试

# 3. 部署
agentcore launch

# 4. 生产管理
aws bedrock-agentcore-control list-agent-runtimes
```

## 注意事项

1. **配置文件冲突**：多个智能体在同一目录时，避免重复运行 `configure`
2. **权限管理**：确保执行角色有足够的权限访问所需资源
3. **网络配置**：生产环境建议配置VPC和安全组
4. **成本控制**：定期清理未使用的资源，监控调用量
5. **版本管理**：使用标签管理不同版本的智能体运行时

## 相关文档

- [AWS AgentCore 官方文档](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS CLI 参考](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/)
- [AgentCore Runtime 指南](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html)