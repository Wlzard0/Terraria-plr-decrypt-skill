# Terraria .plr 存档格式（v319，1.4.5.x）

来源：反编译 Terraria 1.4.5.6 的 `Player.Serialize/Deserialize`、`CreativePowerManager`、
`EquipmentLoadout`、`ItemsSacrificedUnlocksTracker`、`CraftingRequests`，并对真实存档逐字节验证。
全部小端序。以下为 v319 顺序；括号内为版本门槛（`vNNN+` 表示该字段仅在该版本号起存在）。

## 加密

- AES-128-CBC，Key = IV = `h3y_gUyZ` 的 UTF-16LE 字节（`6800330079005F006700550079005A00`），无填充，密文长度须为 16 的倍数。
- 解密后自检头部：`int32 版本 + b"relogic" + byte 3`。

## 头部

| 字段 | 类型 | 版本 | 说明 |
| --- | --- | --- | --- |
| version | int32 | 全部 | 319=1.4.5.x，279=1.4.4.9，194=1.3.5.3 |
| magic | 7B | 全部 | 固定 `relogic` |
| fileType | byte | 全部 | 固定 3 |
| revision | uint32 | 全部 | 通常 0 |
| favorite | uint64 | 全部 | 通常 0 |
| name | 7bit 长度 + UTF-8 | 全部 | 角色名 |
| difficulty | byte（v17+；v10–16 为 bool 硬核） | ≥10 | 0 经典/1 中核/2 硬核/3 旅途 |
| playTime | int64 | ≥138 | .NET TimeSpan ticks（10,000,000/s） |
| hair | int32 | 全部 | 发型 ID |
| hairDye | byte | ≥82 | 发饰染料 |
| team | byte | ≥283 | **PvP 队伍编号**（1.4.5 新增，旧资料曾误标为“extra_v315”） |
| hideVisibleAccessory | byte×2 | ≥124 | 位掩码，槽 0–9 外观隐藏；v83–123 只有 1 字节 |
| hideMisc | byte | ≥119 | 位掩码，bit0=隐藏杂项 |
| skinVariant | byte | ≥107 | 0–3 男，4–9 女；<107 读 bool male |
| health/healthMax/mana/manaMax | int32 ×4 | 全部 | 生命/魔力 |
| extraAccessory | bool | ≥125 | 恶魔之心 |
| unlockedBiomeTorches / usingBiomeTorches | bool ×2 | ≥229 | 生物群系火把 |
| ateArtisanBread | bool | ≥256 | 工匠面包 |
| usedAegisCrystal/Fruit/ArcaneCrystal/GalaxyPearl/GummyWorm/Ambrosia | bool ×6 | ≥260 | 永久强化 |
| downedDD2EventAnyDifficulty | bool | ≥182 | 旧日军团 |
| taxMoney | int32 | ≥128 | 税钱（铜币） |
| numberOfDeathsPVE / PVP | int32 ×2 | ≥254 | 死亡数 |
| 7 × RGB | 3B ×7 | 全部 | 发/肤/瞳/上衣/内衬/裤/鞋颜色 |

## 物品与主体

物品编码：装备/染料/杂项 = `int32 ID + byte 词缀`（5B）；背包/钱币/弹药 = `int32 ID + int32 数量 + byte 词缀 + byte 收藏`（10B）；仓库/配装 = `int32 ID + int32 数量 + byte 词缀`（9B）。空槽同样占满。

顺序：装备 20×5B → 染料 10×5B → 主背包 50×10B → 钱币 4×10B → 弹药 4×10B → 杂项 5×(5+5)B → 猪猪存钱罐 40×9B → 保险箱 40×9B → 护卫熔炉 40×9B（v182+）→ 虚空袋 40×10B（v269+；v198–268 为 9B）→ downedDeerclops bool（v200+）→ 增益 44×(8B)（v269+；旧版 22）→ 出生点循环（int32 x；x=-1 结束；否则 y、worldID、worldName）→ hotbarLocked bool → hideInfo 13×bool（v145+）→ anglerQuestsFinished int32 → 手柄方向键绑定 4×int32（v255+）→ 建造开关 12×int32（v230+；v200+ 11 个；更早 10 个）。

## 中后段（旧资料误称“中间段/未公开区”）

| 字段 | 类型 | 版本 | 说明 |
| --- | --- | --- | --- |
| bartenderQuestLog | int32 | ≥181 | 酒馆老板任务数（旧资料误称 `qd`） |
| dead | bool | ≥200 | 死亡标记（旧资料误称 `fb`）；true 时再读 respawnTimer int32（旧资料误称 `Ie`） |
| lastTimePlayerWasSaved | int64 | ≥202 | DateTime.ToBinary()（旧资料把高低 4 字节误拆成 `pe`/`qe`） |
| golferScoreAccumulated | int32 | ≥206 | 高尔夫累计得分（旧资料误称 `cb`） |
| research | bool + int32 + 条目 | ≥218 | v282+ 开头多 1 个 bool（读取后丢弃）；然后 int32 数量 + 每条 `字符串 itemName + int32 数量` |
| 临时物品槽 | byte + 每槽 9B | ≥214 | 1 字节位标记，4 个建造饰品槽；置位才读物品 |
| 创造模式权限 | 循环 | ≥220 | `bool 有数据 + uint16 权限ID + 载荷`，以 bool false 结束；1.4.5.6 仅 3 个持久权限：ID 5 godmode=bool、ID 11 远距离放置=bool、ID 14 刷怪率=float |
| superCart | byte | ≥253 | bit0=已解锁超级矿车，bit1=已启用（本样本 0x03 = 两者都开） |
| CurrentLoadoutIndex | int32 | ≥262 | 当前配装 0–2 |
| 配装 ×3 | 280B ×3 | ≥262 | 每块 = 20×物品9B + 10×染料9B + 10×bool 隐藏（旧资料误读为 30×9B + 10×bool，并漏掉配装 1） |
| voiceVariant | byte | ≥280 | 1=男声，2=女声（旧资料误把此字节当成超级矿车） |
| voicePitchOffset | float | ≥281 | 音调偏移 |
| pendingRefunds | int32 + 每项 9B | ≥300 | 待退物品数 + 物品 |
| oneTimeDialoguesSeen | int32 + 字符串 | ≥310 | 一次性对话记录数 + 每条 7bit 长度字符串 |

读取完已知字段后若仍有少量字节（如本样本末尾 1 字节 `01`），1.4.5.6 会忽略，属正常现象，按原始 hex 输出即可，不要臆测。

## 版本差异提示

- v279（1.4.4.9）：无 team、voice、refunds、dialogues；配装 2 块每块 280B；研究段无开头 bool。
- v194（1.3.5.3）：无永久强化、无旅途研究、无配装；buff 22 格。
- 旧资料中的 `extra_v315`、`qd/fb/Ie/pe/qe/cb`、`na 字节`、`中间段` 名称均废弃，勿再使用。
