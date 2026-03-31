---
name: buy-ingredients
description: 查询食材购买信息。当用户要求购买食材、查询某个食材在超市是否有货、提到"买菜"、"买食材"、"M&S有没有"、"去哪买"等时触发。也在 create-recipe 生成菜谱后用户想采购时触发。
---

# Buy Ingredients

根据菜谱或用户指定的食材，通过 Playwright 在 M&S 网站搜索商品并查询附近门店库存。

## Workflow

1. 确定食材来源：
   - 用户指定菜谱名 → 读取 `.recipes/{菜名}.md`，解析 Ingredients 表格提取食材列表
   - 用户直接指定食材 → 直接使用
2. 询问用户是否需要购买调味品（如盐、胡椒、油等常见调味料）：
   - 如用户不需要 → 从食材列表中去除调味品，只查询其余食材
   - 如用户需要 → 保留完整食材列表
3. 询问用户邮编：
   - 必须主动询问，不可跳过
   - 如用户提供邮编 → 记入记忆，传给脚本 `--postcode`
   - 如用户明确表示不需要 → 不传 `--postcode`，仅搜索商品不查门店库存
   - 后续使用 → 从记忆读取邮编，向用户确认是否仍用该邮编
4. 将中文食材名翻译为英文，并参照 `references/marksandspencer/food-catalogue.md` 确定每种食材对应的完整路径（必须走到目录树的最底层叶子节点）
5. 运行脚本（在 `scripts/` 目录下执行）：
   ```
   cd scripts && uv run search_ms.py [--postcode <邮编>] --query "<path>:<英文食材1>,<path>:<英文食材2>,..."
   ```
   - path 为从 category 到最底层叶子节点的完整 slug 路径（小写、空格替换为连字符、`&` 替换为 `and`），例如 `fruit-and-vegetables/fresh-vegetables/root-vegetables/carrots:carrot`、`meat/beef/steaks:steak`
   - M&S 分类页面上有子分类 pill 按钮（如 Root Vegetables 页面有 Beetroot、Carrots、Parsnips 等），这些子分类已记录在 `food-catalogue.md` 中。查询食材时必须使用这些最深层子分类的路径，而非停在父分类
   - 如果在最深层子分类中未搜索到结果，逐层回退父分类重新搜索，直到在某一层找到类似商品即可推荐给用户作为备选项
6. 将脚本输出的结果打印给用户
7. 将查询到的商品记录追加到 `.recipes/bills.csv`：
   - 如果文件不存在，先写入表头：`date,item,price`
   - 每条商品一行：`{当天日期},{商品名},{价格}`
   - 日期格式 `YYYY-MM-DD`，商品名使用 M&S 原文，价格为纯数字（单位 £）
   - 如果商品无价格信息（如缺货），price 留空

## Rules

**食材翻译**
- 由 Claude 在调用脚本前完成中文→英文翻译，脚本只接收英文关键词
- 翻译时使用英国超市常见的商品名称（如"芫荽"→"coriander"而非"cilantro"）

**邮编管理**
- 邮编为可选项，用户不提供时仅搜索商品
- 用户提供后保存到记忆中，后续使用前向用户确认是否仍用该邮编

**输出格式**
- 商品名称使用 M&S 网站原文，不翻译，避免用户找不到
- 使用表格打印结果

**脚本环境**
- 在 `scripts/` 目录下执行 `uv run`，.venv 位于 `scripts/` 目录内
- Playwright 浏览器如未安装，先在 `scripts/` 下运行 `uv run playwright install chromium`

**bills.csv 格式示例**
```csv
date,item,price
2026-03-30,British Chicken Breast Fillets,4.75
2026-03-30,Organic Carrots 1kg,1.35
2026-03-30,Fresh Coriander,0.85
```

## Anti-patterns

- 不要将查询结果写入 recipe 文件 — 库存信息实时变化，每次都需重新查询
- 不要在脚本内做食材翻译 — 翻译由 Claude 负责，脚本只负责搜索
- 不要在用户未提供邮编时强制要求 — 邮编是可选的
- 不要覆盖 bills.csv — 必须追加写入，历史记录不可丢失
