# 参考案例:Redis 内存淘汰策略 · 策略模式

这份文档是一个**已经做完的完整样本**,看一遍能直观感受五阶段工作流跑下来是什么样、各阶段实际花了多少笔墨。新案例不要直接套这里的内容(立论、维度、命名都需要根据项目重写),只学**执行的节奏和判断的颗粒度**。

---

## 输入

- **仓库**:`https://github.com/redis/redis`
- **主题**:内存淘汰策略中关于"策略模式"的部分
- **执行日期**:2026-05-18

## 最终产物

```
笔记/第一章/项目/redis内存淘汰策略/
├── SOP.md           (做案例过程同步沉淀的工作笔记,反推出本 skill)
├── 阅读指南.md       (阶段 5 产出)
└── redis/src/
    ├── evict.c      (主角,~480 行,带中文注释 + 学习注释)
    ├── server.h     (~150 行,精简版,只留 MAXMEMORY_* 宏 + redisServer 主题字段)
    ├── config.c     (~100 行,精简版,只留 maxmemory_policy_enum 注册表)
    └── object.c     (~130 行,精简版,只留 initObjectLRUOrLFU 等)
```

文件树体现了两个约定:
- 保留原仓库子路径 `redis/src/` —— 读者可以一对一对照原仓库
- 案例目录 = 主题命名(`redis内存淘汰策略/`),不是仓库名

---

## 阶段 1 · 调研仓库结构 · 实际执行

**入口反推**:主题"内存淘汰"→ 直接定位 `src/evict.c`。这一步靠常识省了目录浏览。如果是不熟悉的项目,先 `gh api repos/redis/redis/contents/src | jq -r '.[].name'` 列目录,挑最像主题入口的文件名。

**在 evict.c 里 grep 三类符号** → 得到关联文件清单:

| 符号 | grep 出来的文件 | 这个文件扮演什么角色 |
|---|---|---|
| `server.maxmemory_policy`、`MAXMEMORY_*` | `server.h` | 主题身份:常量定义 + 全局状态字段 |
| `maxmemory_policy_enum`(grep 全仓库才找到) | `config.c` | 主题选择:字符串名→枚举的注册表 |
| `->lru` 字段在 evict.c 里多处使用 | `object.c` | 主题对存储的反向影响:lru 字段的初始化和解读 |

**四角色覆盖检查**:
- (a) 主题身份 → `server.h` ✓
- (b) 主题选择 → `config.c` ✓
- (c) 主题使用(主角) → `evict.c` ✓
- (d) 主题对存储的反向影响 → `object.c` ✓

不重复、不遗漏,清单确定下来:4 个文件。

---

## 阶段 2 · 部分下载 · 实际执行

**ref 选择**:本次用了仓库默认分支 `unstable` 的 HEAD(后续如果要追求严格可复现,应该改用 release tag,例 `7.4.0`)。

**命名约定的实际应用**:

| 文件 | 原大小 | 是否主角? | 下载后命名 |
|---|---|---|---|
| `evict.c` | 764 行(整篇都跟主题相关) | ✓ 主角 | 直接 `evict.c` |
| `server.h` | 4622 行(99% 跟主题无关) | ✗ | `server.h.full` |
| `config.c` | 3841 行 | ✗ | `config.c.full` |
| `object.c` | 1949 行 | ✗ | `object.c.full` |

下载命令(示意):
```bash
mkdir -p redis内存淘汰策略/redis/src
curl -sL https://raw.githubusercontent.com/redis/redis/unstable/src/evict.c   \
  -o redis内存淘汰策略/redis/src/evict.c
curl -sL https://raw.githubusercontent.com/redis/redis/unstable/src/server.h  \
  -o redis内存淘汰策略/redis/src/server.h.full
# ... 另外两个同理
```

**回看**:`.full` 后缀这条约定在阶段 3 里立刻见效——精简时打开 `server.h.full` 和 `server.h` 做左右对照,做完直接 `rm *.full`。这条约定值得**固化进 skill**。

---

## 阶段 3 · 精简代码 · 实际执行

精简前后对照:

| 文件 | 原行数 | 精简后 | 砍掉了什么 |
|---|---|---|---|
| `server.h` | 4622 | ~150 | 命令表、AOF、复制、集群、ACL、TLS、Lua、模块相关 |
| `config.c` | 3841 | ~100 | 几百条其它配置项注册、解析与重载逻辑、CONFIG GET/SET 命令实现 |
| `object.c` | 1949 | ~130 | 对象创建/销毁/编码转换的其它工具、共享对象、`MEMORY USAGE` |
| `evict.c` | 764 | ~480 | 没删主题代码,只删 ASCII art 框线、重复说明、版权头细节 |

### server.h 保留细节(作为"精简到位"的范例)

保留的段落:
- `MAXMEMORY_FLAG_*` / `MAXMEMORY_*` 全部 10 个宏(原 line 685~701)
- `redisServer` 中 6 个主题字段(原 line 2417~2425)
- `configEnum` 类型定义(原 line 3928~3931)
- `LFU_INIT_VAL` 与 `EVICT_*` 常量(原 line 4214~4220)
- evict.c 的对外函数声明 6 个

**`redisServer` 结构体的处理**特别能体现"删字段但保结构"的精简手法:原本几百个字段全部省略,只保留 6 个 `maxmemory*` / `lfu_*` 字段。占位写法:
```c
struct redisServer {
    /* ... (省略约 200 个非淘汰相关字段:网络、复制、集群、ACL、AOF、Lua...) ... */

    /* 内存淘汰相关字段 —— 本主题保留 */
    unsigned long long maxmemory;
    int maxmemory_policy;
    int maxmemory_samples;
    int lfu_log_factor;
    int lfu_decay_time;
    /* ... (省略剩余字段) ... */
};
```

### "删够了"的硬验收

每个文件读完用一句话回答它的角色:
- `server.h`:策略的【枚举身份】+ 客户端持有
- `config.c`:字符串名→枚举的【注册表】(编译期静态)
- `evict.c`:★ 客户端主流程,if/else 分发 + 工具函数
- `object.c`:策略决定 24bit 字段的【存储格式】+ 外部命令约束

四句话都说得出 → 精简到位。

---

## 阶段 4 · 翻译 + 学习注释 · 实际执行

每个文件头都加了三段式"学习注释 / 精简说明"块。例(evict.c 的开头):

```
============================================================
学习注释 / 精简说明

【原文件】src/evict.c · 764行 · 内存淘汰核心逻辑

【本主题保留】
  几乎全部代码(本文件是主角),仅删除 ASCII art 框线、重复
  英文段落和版权头细节。

【本主题删除】
  无主题相关代码删除。

【对比锚点】
  对应 Linux TCP 案例的 net/ipv4/tcp_input.c —— 都是"策略
  客户端主流程"所在文件。两者的差异是本案例的核心论点:
  TCP 用 `icsk_ca_ops->cong_avoid(...)` 调用,这里却用
  `if (policy & FLAG_LRU) { ... }` 大分发。
============================================================
```

**`★` 标注的实际分布**(全案例 6 处 `★★★`):
1. `performEvictions()` 的分发结构(evict.c)
2. `performEvictions()` 内分发分支 A:LRU/LFU/TTL 路径(evict.c)
3. `performEvictions()` 内分发分支 B:RANDOM 路径(evict.c)
4. `evictionPoolPopulate()` 的 idle 三种含义(evict.c)
5. `initObjectLRUOrLFU()` 的 4 行存储格式分支(object.c)
6. 对所有这些代码"为什么 if/else 而不是函数指针"的总结(evict.c)

注意 `★★★` 集中在主角文件(evict.c 占 4 个),辅助文件 1 个,头文件 0 个——**主角戏份最多很合理**。

**翻译的"再加工"实例**:

- 原文:
  > /* Note that we should also try to do this in a way that is friendly to the CPU cache, because random reads from a big hash table can be slow. */
- 再加工后:
  > /* 也要照顾 CPU 缓存——大哈希表的随机读很慢。 */

3 行变 1 行,意图保留,扫读速度翻倍。整篇 evict.c 这么压一遍,加起来大约从原 764 行变成 480 行(其中砍掉的非主题代码不到 100 行,剩下 100+ 行都是注释压缩)。

---

## 阶段 5 · 写阅读指南 · 实际执行

完整的阅读指南.md 在原项目目录里。这里只列**结构决策**:

- **立论**(写在"这堆文件想让你看到什么"开头):
  > 策略模式在工程里【不总是函数指针表】。在追求内存与性能的场景下,它退化成了"一个 int 枚举 + if/else 分发"。

- **建议阅读顺序**(5 站):
  1. 策略的"身份"——10 种策略的编码(server.h)
  2. 策略的"注册表"——字符串名 → 内部枚举(config.c)
  3. 策略的"主角"——performEvictions(evict.c 主段)
  4. 再看一次策略分发的细节——evictionPoolPopulate(evict.c 次段)
  5. 策略对存储格式的影响——initObjectLRUOrLFU(object.c)

  注意:**两次回到 evict.c**(站 3 和站 4),因为主角文件信息密度高、要分两步看。这种"跨文件交错"的顺序就是"按认知路径而非目录顺序"的体现。

- **差异表的 8 个维度**(对照 Linux TCP):

  | 维度 |
  |---|
  | 策略对象的形态 |
  | 客户端代码是否出现具体策略名 |
  | 客户端调用方式 |
  | 新增策略是否需要改客户端 |
  | 注册方式(运行时 vs 编译期) |
  | 策略持有粒度(每连接 vs 全局) |
  | 策略是否影响存储格式 |
  | 设计目标 |

  这 8 个维度的关键属性:**每个维度的两列答案都明显不同**。如果某个维度两列答案相同或相近,那个维度对案例没价值,应该换。

- **练习题**:
  > 如果我要给 Redis 新增一种淘汰策略,叫 `volatile-fifo`(优先淘汰先写入的带 TTL 的 key),需要改哪几个文件?分别改什么?

  答案对应到 4 个文件(server.h / config.c / evict.c / 可选 object.c),关键论点是**必须改 evict.c 客户端代码**——而 Linux TCP 同样的题答案是"不需要改任何客户端代码"。这一对差异就是整篇案例的核心论点。

---

## 这个案例反推出的五条 skill 规则

这五条已经写进 SKILL.md 主文档,这里只列名字方便回顾:

1. 入口反推法
2. `.full` 后缀约定
3. `★` / `★★★` 标注主题命中点
4. 必备产出表格两张(文件角色对照表 + 差异表)
5. 结尾留一道"加一个新 X 要改哪里"的练习题

**做新案例时**:先把这五条规则在心里过一遍,确保你的产物覆盖了它们。如果某条规则你的案例做不到(例:对照案例还没写,差异表写不出),先去写对照案例,而不是糊弄。
