# Terraria .plr 存档格式（v319–v326，1.4.5.6–1.4.5.8）

来源：反编译 Terraria 1.4.5.6 的 `Player.Serialize/Deserialize`、`CreativePowerManager`、
`EquipmentLoadout`、`ItemsSacrificedUnlocksTracker`、`CraftingRequests`，以及 Terraria
1.4.5.8 的 `Player.Serialize/Deserialize` 和 `EquipmentLoadout`；已用真实 v326 存档逐字节验证。
全部小端序。v319 是基础顺序；v322+、v324+ 与 v326 的覆盖规则见下文。括号内为版本门槛
（`vNNN+` 表示该字段仅在该版本号起存在）。

## 加密

- AES-128-CBC，Key = IV = `h3y_gUyZ` 的 UTF-16LE 字节（`6800330079005F006700550079005A00`），密文长度须为 16 的倍数。
- 1.4.5.8 的写入端通过 `RijndaelManaged` / `CryptoStream` 写入，末块使用 PKCS#7 填充。若以原始 CBC 解密而未去填充，已解析的玩家负载后可能出现 `n` 个值均为 `n` 的字节（`n=1..16`）；例如 v326 测试档的末尾 `04 04 04 04` 是 4 字节填充，不是游戏字段。
- 解密后自检头部：`int32 版本 + b"relogic" + byte 3`。

## 头部

| 字段 | 类型 | 版本 | 说明 |
| --- | --- | --- | --- |
| version | int32 | 全部 | 326=1.4.5.8，319=1.4.5.6，279=1.4.4.9，194=1.3.5.3 |
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
| reservedV324 | bool | ≥324 | 1.4.5.8 的序列化代码固定写入 `false`，反序列化时读取后丢弃；应保留/跳过该占位字节，不应解释为角色进度。 |
| usedAegisCrystal/Fruit/ArcaneCrystal/GalaxyPearl/GummyWorm/Ambrosia | bool ×6 | ≥260 | 永久强化 |
| downedDD2EventAnyDifficulty | bool | ≥182 | 旧日军团 |
| taxMoney | int32 | ≥128 | 税钱（铜币） |
| numberOfDeathsPVE / PVP | int32 ×2 | ≥254 | 死亡数 |
| 7 × RGB | 3B ×7 | 全部 | 发/肤/瞳/上衣/内衬/裤/鞋颜色 |

## 物品与主体

物品编码：装备/染料/杂项 = `int32 ID + byte 词缀`（5B）；背包/钱币/弹药 = `int32 ID + int32 数量 + byte 词缀 + byte 收藏`（10B）；仓库/配装 = `int32 ID + int32 数量 + byte 词缀`（9B）。空槽同样占满。v322+ 的装备、染料和配装项另有收藏标记覆盖规则，见“v322–v326 已验证增补”。

顺序：装备 20×5B → 染料 10×5B → 主背包 50×10B → 钱币 4×10B → 弹药 4×10B → 杂项 5×(5+5)B → 猪猪存钱罐 40×9B → 保险箱 40×9B → 护卫熔炉 40×9B（v182+）→ 虚空袋 40×10B（v269+；v198–268 为 9B）→ downedDeerclops bool（v200+）→ 增益 44×(8B)（v269+；旧版 22）→ 出生点循环（int32 x；x=-1 结束；否则 y、worldID、worldName）→ hotbarLocked bool → hideInfo 13×bool（v145+）→ anglerQuestsFinished int32 → 手柄方向键绑定 4×int32（v255+）→ 建造开关 12×int32（v230+；v200+ 11 个；更早 10 个）。

## v322–v326 已验证增补（1.4.5.8）

| 版本门槛 | 位置 | 读取/写入规则 | 作用 |
| --- | --- | --- | --- |
| v322+ | 主装备 `armor[20]` | 每槽从 `int32 ID + byte prefix`（5B）变为再附加 `bool favorited`（6B）。 | 收藏的装备可供其他配装共享。 |
| v322+ | 主染料 `dye[10]` | 每槽同样从 5B 变为 6B，末尾为 `bool favorited`。 | 收藏的染料可供其他配装共享。 |
| v322+ | 三套 `EquipmentLoadout` | 每套由 280B 变为 310B：`20×(ID+数量+词缀+收藏，10B)` + `10×(ID+数量+词缀+收藏，10B)` + `10×bool Hide`。 | 配装内的收藏状态必须逐槽保存。 |
| v324+ | `ateArtisanBread` 之后、六项永久强化之前 | 读取/写入 1 个 `bool reservedV324`；1.4.5.8 写入端固定写 `false`，读取端不保留其值。 | 兼容性占位，不是可见角色状态。 |
| v326 | 文件头 `version` | 1.4.5.8 写入 `326`，加载端把大于 326 的版本标为较新版本。`Player.Deserialize` 没有额外的 v326 玩家字段门槛。 | 当前 1.4.5.8 玩家存档版本。 |

因此，用仅支持 v319 的读取器直接读取 v326 时，会先漏掉主装备/染料的 30 个收藏字节及 `reservedV324` 的 1 字节，随后在三套配装中再漏掉 90 个收藏字节，造成后续字段整体错位。

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
| 配装 ×3 | 280B ×3（v262–321）；310B ×3（v322+） | ≥262 | v262–321：每块 = 20×物品9B + 10×染料9B + 10×bool 隐藏；v322+：30 个物品项都追加 `bool favorited`。旧资料曾误读为 30×9B + 10×bool，并漏掉配装 1。 |
| voiceVariant | byte | ≥280 | 1=男声，2=女声（旧资料误把此字节当成超级矿车） |
| voicePitchOffset | float | ≥281 | 音调偏移 |
| pendingRefunds | int32 + 每项 9B | ≥300 | 待退物品数 + 物品 |
| oneTimeDialoguesSeen | int32 + 字符串 | ≥310 | 一次性对话记录数 + 每条 7bit 长度字符串 |

读取完已知字段后，先检查剩余字节是否为合法 PKCS#7 填充；例如 v326 测试档的 `04 04 04 04` 应去填充后视为文件结束。填充长度随负载长度变化（1–16 字节）：某 v326 样本（明文 3840 B）的负载为 3831 B，末尾是 9 个 `09`。若剩余字节不是合法填充，按原始 hex 输出并注明为未读取数据，不要臆测其含义。

## 版本差异提示

- v279（1.4.4.9）：无 team、voice、refunds、dialogues；配装 2 块每块 280B；研究段无开头 bool。
- v194（1.3.5.3）：无永久强化、无旅途研究、无配装；buff 22 格。
- v326（1.4.5.8）：适用 v322+ 的装备/染料/配装收藏标记与 v324+ 的保留 bool；文件头为 326，但没有额外 v326 玩家字段。
- 旧资料中的 `extra_v315`、`qd/fb/Ie/pe/qe/cb`、`na 字节`、`中间段` 名称均废弃，勿再使用。
