#!/bin/bash
# Initialize default configuration for link-researcher skill

CONFIG_DIR="$HOME/.config/linky"

# Create directory structure
mkdir -p "$CONFIG_DIR/personas"
mkdir -p "$CONFIG_DIR/templates"
mkdir -p "$CONFIG_DIR/good-shots"
mkdir -p "$CONFIG_DIR/output-styles"
mkdir -p "$CONFIG_DIR/sessions"
mkdir -p "$CONFIG_DIR/domains"

# Write default config if not exists
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
cat > "$CONFIG_DIR/config.toml" << 'TOML'
# Linky 配置文件
# 修改此文件来自定义分析行为

# 默认输出方式: "notion" | "markdown" | "multi-file" | "prompt"
default_output = "markdown"

# 默认输出风格: "standard" | "极简白话" | "explanatory" | "learning"
# 输出方式决定投递到哪里，输出风格决定用什么口吻和结构写
output_style = "standard"

# 输出目录（markdown/multi-file 模式），留空则使用当前工作目录
output_dir = ""

# 默认语言
language = "zh-CN"

# 每批处理的链接数量上限
batch_size = 15

# 分析时包含的视角，逗号分隔
# 可选: tech, product, investment, content-creator
# 设为 "all" 则全部启用
perspectives = "all"

[notion]
# 目标页面 ID 或数据库 ID（使用 Notion 输出时需配置）
target_page_id = ""
# 是否同时创建数据库条目
create_database_entries = false

[extraction]
# 采集策略由 fetch-strategy.toml 单独管理
# 该文件定义降级链、域名路由、选择器等
# 仓库预设会在 init 时拷贝到此目录，你可以自由修改
# strategy_file = "fetch-strategy.toml"

[prompt_mode]
# 是否在 prompt 中包含完整正文（false 则只包含摘要，更精简）
include_full_text = false
TOML
echo "Created default config at $CONFIG_DIR/config.toml"
fi

# Migrate from yaml if exists
if [ -f "$CONFIG_DIR/config.yaml" ] && [ ! -f "$CONFIG_DIR/.migrated" ]; then
  echo "Note: Found old config.yaml. Please migrate settings to config.toml manually."
  echo "  Old: $CONFIG_DIR/config.yaml"
  echo "  New: $CONFIG_DIR/config.toml"
  touch "$CONFIG_DIR/.migrated"
fi

# Write default persona if not exists
if [ ! -f "$CONFIG_DIR/personas/default.md" ]; then
cat > "$CONFIG_DIR/personas/default.md" << 'MD'
# 默认分析视角

分析每个链接时，综合以下视角给出判断：

## 技术视角
- 技术可行性、架构质量、技术栈选择
- 代码质量、维护性、社区活跃度

## 产品视角
- 市场定位、用户价值、产品成熟度
- 与竞品的差异化

## 投资/趋势视角
- 是否代表某个趋势
- 商业模式是否可持续
- 团队/社区的增长势头

## 内容创作视角
- 是否适合作为选题素材
- 信息密度和原创性
- 是否值得二次创作或引用

根据链接的具体类型，侧重最相关的 1-2 个视角。
MD
echo "Created default persona at $CONFIG_DIR/personas/default.md"
fi

# Migrate old preferences.md into memory.md if exists
if [ -f "$CONFIG_DIR/preferences.md" ]; then
  echo ""
  echo "Note: preferences.md is deprecated — merge its content into memory.md manually."
  echo "  Old: $CONFIG_DIR/preferences.md"
  echo "  New: $CONFIG_DIR/memory.md (User Preferences / Analysis Rules sections)"
fi

# Create output-adapters directory
mkdir -p "$CONFIG_DIR/output-adapters"

# Write output-styles README if directory is empty
if [ ! -f "$CONFIG_DIR/output-styles/README.md" ]; then
cat > "$CONFIG_DIR/output-styles/README.md" << 'MD'
# Output Styles — 自定义输出风格

把自定义输出风格放在这里，文件名就是可配置的风格名。

内置风格在 Linky 仓库的 `references/output-styles/`：

- `standard`
- `极简白话` / `minimal_plain`
- `explanatory`
- `learning`

自定义文件格式：

```markdown
---
id: my_style
name: My Style
description: Short description
keep-research-instructions: true
render-mode: standard
---

这里写追加给 Linky 的输出风格指令。
```

同名自定义风格优先于仓库内置风格。
MD
echo "Created output-styles README at $CONFIG_DIR/output-styles/README.md"
fi

# Write good-shots README if directory is empty
if [ ! -f "$CONFIG_DIR/good-shots/README.md" ]; then
cat > "$CONFIG_DIR/good-shots/README.md" << 'MD'
# Good Shots — 优质输出示例

将你认可的输出示例放在这里，按链接类型命名：

- `github-repo.md` — Git 仓库的理想输出
- `product.md` — 产品官网的理想输出
- `article.md` — 文章/博客的理想输出
- `video.md` — 视频的理想输出
- `social-media.md` — 社媒帖文的理想输出
- `docs-tutorial.md` — 文档/教程的理想输出
- `platform.md` — 导航站/平台的理想输出

这些示例会被 skill 读取，作为生成分析卡时的质量标杆。
MD
echo "Created good-shots README at $CONFIG_DIR/good-shots/README.md"
fi

# Copy default fetch-strategy.toml if not exists
# 用户可修改此文件覆盖仓库中的默认采集策略
if [ ! -f "$CONFIG_DIR/fetch-strategy.toml" ]; then
  SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
  if [ -f "$SKILL_DIR/references/fetch-strategy.toml" ]; then
    cp "$SKILL_DIR/references/fetch-strategy.toml" "$CONFIG_DIR/fetch-strategy.toml"
    echo "Created fetch strategy at $CONFIG_DIR/fetch-strategy.toml"
  fi
fi

# Copy user-profile template if not exists
if [ ! -f "$CONFIG_DIR/user-profile.toml" ]; then
  SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
  if [ -f "$SKILL_DIR/references/user-profile-template.toml" ]; then
    cp "$SKILL_DIR/references/user-profile-template.toml" "$CONFIG_DIR/user-profile.toml"
    echo "Created user profile at $CONFIG_DIR/user-profile.toml"
  fi
fi

# Write memory file if not exists
if [ ! -f "$CONFIG_DIR/memory.md" ]; then
cat > "$CONFIG_DIR/memory.md" << 'MD'
# Linky Memory

唯一的通用记忆入口。由 skill 自动维护 + 用户可编辑。

## User Preferences

## Analysis Rules

## Accounts

## Global Notes

MD
echo "Created memory file at $CONFIG_DIR/memory.md"
fi

echo ""
echo "Linky config initialized at $CONFIG_DIR"
echo ""
echo "Directory structure:"
echo "  $CONFIG_DIR/"
echo "  ├── config.toml            # 全局设置"
echo "  ├── user-profile.toml      # 注册偏好（用户名、邮箱等）"
echo "  ├── fetch-strategy.toml    # 采集策略（覆盖仓库默认）"
echo "  ├── memory.md              # 通用记忆（偏好、账号、经验）"
echo "  ├── personas/              # 分析视角"
echo "  │   └── default.md"
echo "  ├── templates/             # 自定义分析卡模板"
echo "  ├── output-styles/         # 自定义输出风格"
echo "  ├── good-shots/            # 优质输出示例"
echo "  │   └── README.md"
echo "  ├── sessions/              # 本地授权上下文缓存（自动管理，不写入报告）"
echo "  ├── domains/               # 域名记忆（访问历史 + trace）"
echo "  └── output-adapters/       # 自定义输出适配器脚本"
