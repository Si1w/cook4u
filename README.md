# cook4u

基于 Claude Code Skill 的烹饪助手，帮助生成菜谱和在 M&S 超市查找食材。

## 安装

将本项目克隆到本地，然后在 Claude Code 设置中将项目路径添加为 Skill 目录。

## Skills

### create-recipe

根据用户需求生成结构化菜谱，输出 Markdown 文件到 `.recipes/`，包含食材表格和分步骤说明。

### buy-ingredients

在 M&S Foodhall 网站搜索食材，获取实时价格和库存信息。

- 使用 Playwright 自动化搜索 M&S 网站
- 参照 food catalogue 导航到最精确的分类页面
- 支持通过邮编选择附近门店，获取本地价格和库存
- 通过 cookie 持久化门店选择，加速后续搜索

## 使用方式

在 Claude Code 中直接对话触发：

- "帮我做一道番茄炒蛋" → 触发 create-recipe
- "帮我查一下 M&S 有没有胡萝卜" → 触发 buy-ingredients

也可以通过斜杠命令触发：

- `/create-recipe` — 创建菜谱
- `/buy-ingredients` — 查询食材