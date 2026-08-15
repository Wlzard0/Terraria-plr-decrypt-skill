# terraria-plr-decrypt

Terraria 角色存档（`.plr`）解密与分析技能，供 Codex / ChatGPT 使用。

## 功能特性

- AES-128 解密（纯 Python 实现，离线可用，无第三方依赖）
- 完整解析 Terraria 1.4.5.x（存档版本 319）全部字段，旧版本（279 / 194）尽力兼容
- 内置中文物品、增益、前缀名称对照
- 输出可读文本报告与 JSON 数据，方便查看背包、装备、增益及字段含义
- 只读分析：不修改存档文件，不保存解密副本

## 快速安装

在 Codex 对话中发送：

```
$skill-installer install https://github.com/<你的用户名>/terraria-plr-decrypt/tree/main/skills/terraria-plr-decrypt
```

详细安装步骤见 [INSTALL.md](INSTALL.md)。

## 使用方法

把存档文件路径交给 Codex 即可，例如：

- “帮我解密这个存档：`C:\...\I_Am_a_Rock.plr`，然后告诉我里面有什么”
- “解析这个 `.plr` 文件，列出我的背包和装备”
- “解释这个 `.plr` 存档里的某个字段是什么意思”

## 目录结构

```
terraria-plr-decrypt/
├── SKILL.md                  # 技能入口与使用流程
├── agents/
│   └── openai.yaml           # Codex UI 元数据
├── scripts/
│   └── parse_plr.py          # 解密与解析脚本（纯 Python，无第三方依赖）
└── references/
    ├── format.md             # v319 字段格式与版本说明
    └── names.md              # 中文物品/增益/前缀名称对照
```

## 兼容性

- 完全支持：Terraria 1.4.5.x（存档版本 319）
- 尽力支持：旧版本 279 / 194
- 运行环境：Python 3，离线可用，无需安装第三方包

## 许可

MIT License，见 [LICENSE](LICENSE)。
