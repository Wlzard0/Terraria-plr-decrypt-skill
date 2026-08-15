# 安装说明

## 环境要求

- Codex（桌面版或 CLI）或支持 Agent Skills 的客户端
- Python 3（解析脚本运行环境）

## 方法一：通过 $skill-installer 安装（推荐）

在 Codex 对话中发送：

```
$skill-installer install https://github.com/<你的用户名>/terraria-plr-decrypt/tree/main/skills/terraria-plr-decrypt
```

Codex 会自动把技能下载到 `$CODEX_HOME/skills/terraria-plr-decrypt`（Windows 通常是 `C:\Users\<你的用户名>\.codex\skills\`）。安装完成后，从下一轮对话开始生效。

## 方法二：手动安装

1. 下载本仓库：点击页面右上角 **Code → Download ZIP**，或运行 `git clone https://github.com/<你的用户名>/terraria-plr-decrypt.git`
2. 把 `skills/terraria-plr-decrypt` 整个文件夹复制到本机技能目录：
   - Windows：`C:\Users\<你的用户名>\.codex\skills\`
   - macOS / Linux：`~/.codex/skills/`
3. 重启 Codex

## 验证是否安装成功

在 Codex 中询问：

> 你能解密和分析 Terraria 的 `.plr` 存档吗？

如果技能已生效，Codex 会提到或直接调用解密分析流程。

## 使用示例

把 `.plr` 文件路径发给 Codex，例如：

> 帮我解密 `C:\Users\Documents\My Games\Terraria\Players\I_Am_a_Rock.plr`，并按存档格式说明里面有什么。

Codex 会调用解析脚本生成报告，并用中文总结内容。

## 卸载

删除技能目录中的 `terraria-plr-decrypt` 文件夹，重启 Codex 即可。

## 常见问题

- **安装命令报错**：确认仓库已公开，且 URL 路径正确（`tree/main/skills/terraria-plr-decrypt`）。
- **私密仓库**：需要 GitHub 凭据或 `GITHUB_TOKEN`，建议直接公开仓库。
- **技能不触发**：重启 Codex，或检查 `terraria-plr-decrypt` 文件夹是否位于技能目录下且结构完整。
