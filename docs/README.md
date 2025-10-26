# 文档构建说明

本项目支持中英文双语文档，每个语言版本都是独立的。

## 目录结构

```
docs/
├── changelog.md          # 公共变更日志
├── zh/                   # 中文文档
│   ├── api/             # API 文档
│   ├── guide/           # 用户指南
│   ├── index.md         # 首页
│   ├── quickstart.md    # 快速开始
│   ├── examples.md      # 示例
│   └── development.md   # 开发指南
└── en/                   # 英文文档
    ├── api/             # API documentation
    ├── guide/           # User guide
    ├── index.md         # Home
    ├── quickstart.md    # Quick start
    ├── examples.md      # Examples
    └── development.md   # Development
```

## 构建命令

### 中文版本（默认）
```bash
PYTHONPATH=src mkdocs build --clean
```

### 英文版本
```bash
PYTHONPATH=src mkdocs build --config-file mkdocs.en.yml --clean
```

### 本地预览

#### 中文版本
```bash
PYTHONPATH=src mkdocs serve
```

#### 英文版本
```bash
PYTHONPATH=src mkdocs serve --config-file mkdocs.en.yml
```

## 部署

文档会构建到 `site/` 目录下，可以直接部署到静态网站托管服务。