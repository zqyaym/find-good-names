# find-good-names

# 朱姓水金姓名生成器

按现成汉字五行标注，程序枚举“朱＋水字＋金字”，不按偏旁限制字库，不调用大模型生成名字。

## 运行

Python 3.9+，无第三方 Python 依赖。首次下载需要访问 GitHub raw。

```bash
python3 download_data.py
python3 generate_names.py
```

先打开 `results/姓名候选预览.md`；完整初筛候选在 `results/filtered_candidates.json`。

```bash
python3 generate_names.py --min-usage 60 --max-rarity 1 --max-gender-bias 0.3 --preview 60
```

## 用户需求

- 朱姓女孩、双字名，水属性字在前，金属性字在后。
- 属性采用现成标注，而非要求氵、钅偏旁。
- 程序穷举，避免模型直接提出少数名字造成探索范围受限。
- 保留来源、冲突和完整候选，支持后续 Agent 修改规则。
- 不重新推算八字，不额外加入三才五格或笔画吉凶约束。

## 来源与标注边界

1. https://github.com/theajack/cnchar ：五行主表，`info.json` 配合 `five-element.json` 解码。
2. https://github.com/James88/qiming ：五行比对表，`data/wuxing_dict_jianti.json`。
3. https://github.com/cicbyte/ai-chinese-naming ：拼音、声调、性别倾向与语义辅助字段。

第三份数据的五行来自 cnchar，不是第三个独立来源。前两库是否相互独立尚未证明；一致只表示表间一致。五行是传统姓名学分类，不是统一的科学属性。

适用度、稀有程度、字义、风格等辅助字段包含第三方 AI 离线标注；它们只参与可调整的初筛。`dupRisk` 不是真实人口重名统计，本程序不使用它排序。完整机械组合不受这些评分过滤。

公开代码不包含第三方数据快照；下载脚本从上游获取。上游各自的许可适用于其数据，尤其 qiming 数据的再分发许可尚未确认。不要把本项目视为对第三方数据的重新授权。`sources.json` 保存 URL 和已验证快照 SHA256；上游内容改变时下载器会停止，需复核再更新散列。

## 已运行的基线

辅助字典 6,777 字；两表一致的水字 1,398、金字 1,350；全组合 1,887,300。
默认初筛 103 个水字和 115 个金字，组合 11,845；规则排除 229，余 11,616；预览 48。

## Agent 接手说明

当前是可复现的初版，不是完成质量验收的姓名推荐。

优先改进：
1. 复核五行来源、读音与字义；冲突单独保留，不按偏旁补判。
2. 女孩适用性默认筛选偏宽：出现“朱雄悦、朱豪倩”等组合，需要改善。
3. 单字分数高不代表搭配自然；多样性算法也可能选出不自然组合。
4. 谐音表很小，只覆盖部分普通话组合，未系统检查粤语或多音字。
5. 宽候选始终保留，将严格筛选做成独立视图，避免重新收窄创意空间。

默认排序是适用度、声调变化、女性倾向的启发式；预览对已使用字扣分以分散选字。不是吉凶分、经过验证的姓名质量分或真实重名率。

## 输出

- `character_audit.json`：逐字标注及来源比对。
- `conflicts_or_missing.json`：分歧或缺失。
- `all_combinations.txt`：188 万机械组合，并不保证适合命名。
- `filtered_character_pools.json`、`filtered_candidates.json`：初筛字池与姓名。
- `rejected_pairs.json`：规则排除原因。
- `preview.json`、`姓名候选预览.md`：分散选字的预览。
- `stats.json`、`source_hashes.json`：参数、数量、快照散列。
