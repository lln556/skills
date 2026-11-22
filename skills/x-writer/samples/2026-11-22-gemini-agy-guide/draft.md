# 草稿：Google One 会员 × Antigravity 避坑指南（教程长文）

> 文体：教程长文（X Article + 钩子推）
> 素材：Mac 浏览记录；Mac、dev 容器、零刻三台机器的 agy 配置和日志；agy / Claude Code / Codex 会话；Antigravity 官方 FAQ 和条款（2026-11-22 核实）
> 上一版：samples/2026-11-22-gemini-agy/draft.md（经验帖）

---

## 钩子推

用了一个多月 Google One 会员加 Antigravity，Mac、Docker 容器、零刻小主机三台都装了一遍，坑比我想的多。

网络、更新、额度、生图生视频、Colab、条款，每个坑都配了我的实测数字，还有能直接丢给 agent 的指令。

全文约 4000 字，先收藏 👇

---

## X Article 正文

### 标题

Google One 会员 × Antigravity 避坑指南：三台机器踩出来的网络、额度和出片经验

### 正文

有一次在 Mac 上更新 agy，后台下了十分钟，下到 55MB 断了，校验失败，界面上看不出原因，再敲 agy update 只会报 update already in progress。

踩完一圈之后再看，同一个会员，5 条竖屏视频只花了 1.8 个 Colab 算力单元，生图一个点数都没扣。

这篇只讲坑和省钱的用法，从零安装和上手就不展开了。

───

# 一、先分清：会员里有好几本账

会员给的不只是 agy 的额度。我这边能用上的还有 Flow 的生图生视频点数、Colab 的算力单元和 Gemini Notebook。

额度：Gemini 和 Claude/GPT 各算各的。

在 agy 里敲 /usage，我这边看到的是两个池子，Gemini 模型一个，Claude 和 GPT 模型一个，各自有 5 小时限额和周限额。不同档位可能不一样，以你自己的 /usage 为准。

[图：/usage 的两个额度池]

登录：agy、Flow、Colab 是三套互不相干的登录。

agy 用的是 agy 自己的登录，Flow 用的是浏览器里登录的账号，Colab CLI 又是单独一套凭据。我这边是 agy 一个号、Flow 一个号、Colab 两个号，有一次问 agy 我之前生图用的是哪个号，它查了一圈才理清楚。

这一步注意：混着用之前，先搞清楚这次扣的是谁的额度。

一键指令：

```
帮我查一下这台机器上 Google 相关工具各自登录的是哪个账号：agy、gcloud、colab CLI（如果装了），以及浏览器里 Flow 用的是哪个。列成表，写清楚每个账号对应哪份额度。只读，不要登出或切换任何账号。
```

───

# 二、网络：TUN 必开，DNS 要理干净

TUN：只开系统代理不够。

agy 的模型请求不走 HTTPS_PROXY，只开系统代理会把真实 IP 漏出去，报 User location is not supported。官方仓库有人提过这个 issue。

所以 Clash 一定要开 TUN 模式。我后来干脆把这条写进了给 agent 的规则里，不许它关 Clash，也不许关 TUN，关了它自己也跑不了。

怎么确认生效了：开着 TUN 启动 agy，随便问一句，能正常回复、不报地区错误就行。

DNS：开了 TUN 还时好时坏，先查这里。

前两天 linux.do 突然打不开，我让 agy 去翻 Mihomo 的日志，最后查出来是 DNS 配置的问题，连环出错：

1. nameserver 里混着明文 UDP 的 223.5.5.5，并发查询时它回得最快，拿回来一个被污染的国内 IP；
2. 这个 IP 在 GeoIP 里是 CN，被排在前面的 GEOIP,CN,DIRECT 判成直连，于是超时；
3. fallback 配的 DoH 本身也是直连出去的，在国内一直超时，污染的缓存刷不掉。

翻历史日志，之前 chat.openai.com 也是这么挂的。Google 的域名走同一套规则，一样会中招。

改法：

- 删掉 nameserver 里的明文 UDP DNS；
- fallback 换成 IP 形式的 DoH，比如 https://1.1.1.1/dns-query，不用先解析域名；
- 打开 respect-rules，让 DNS 查询也按规则走代理；
- 把 GEOIP,CN,DIRECT 挪到 MATCH 前面，别让它排在海外域名规则之前。

这一步注意：Clash Verge 退出时会把内存里的配置写回文件，开着改会被覆盖。先退出 Verge，改完再启动。改之前记得备份。

一键指令：

```
检查我 Clash（Mihomo）的 DNS 和规则配置：nameserver 里有没有明文 UDP DNS；fallback 能不能经代理连通；GEOIP,CN 是不是排在海外域名规则前面。先只读，列出问题和改法，我确认后再改。改之前备份，改的时候先退出 Clash Verge，改完重启并验证。全程不要关闭 Clash 和 TUN。
```

容器里：「没登录」不一定是真掉线。

我在 Docker 容器里跑 agy，隔一阵就提示没登录。翻日志，是刷新 token 的请求 EOF 了，网络断了一下。先查容器的出口通不通，别急着重新登录。

───

# 三、agy 本身：更新、选模型、给自己做个 HUD

更新：别反复敲 agy update。

开头那个坑的原因是这样的。每次启动 agy，它都会拉起一个后台更新进程，锁在这个进程手里，所以你再敲 agy update 就会报 update already in progress。

安装包 62MB 左右，我这边到 Google 只有一百 KB/s 上下，下到 55MB 断了，校验失败，更新包被删掉，结果写进一个文件，界面上什么都不说。我那次是从 1.1.24 更新到 1.5.3，重新触发一轮才下完整。

怎么确认生效了：看 ~/.gemini/antigravity-cli/updater/update_status.json，显示 Update successful 就行，重开终端后 agy --version 能看到新版本号。

一键指令：

```
agy 更新失败了。读 ~/.gemini/antigravity-cli/updater/update_status.json 和最近的更新日志，告诉我失败在哪一步。如果是下载断流，从更新 manifest 里找到当前平台的安装包地址，手动下载、校验后替换 ~/.local/bin/agy，最后跑 agy --version 确认。
```

选模型：日常用 Orchestrator。

Orchestrator 不是一个单独的模型，是强模型先规划、快模型去执行，执行出错了再切回强模型。日常写代码没必要全程用最强的那个，我三台机器上默认都是 Orchestrator。

HUD：别再一遍遍敲 /usage。

我懒得每次都敲 /usage，就让 agy 给自己写了个状态栏脚本。agy 会把 5h 限额、周限额和上下文占用以 JSON 形式推给 statusLine 脚本，TPS 没有现成字段，要从会话日志里算。现在终端底下常驻一行：

```
5h ▰▰▰▰▰ 97% (2h40m)  │  周限 ▰▰▰▰▰ 98% (6d21h)  │  Ctx 11.2% (112k/1M)  │  TPS 53.0 tok/s
```

[图：终端底部的 HUD]

这一步注意：配置里打开 stack_with_default，agy 原生的状态栏会保留，HUD 叠在下面一行。

一键指令：

```
给 agy 写一个 statusLine 脚本：从 stdin 读 JSON，显示当前模型对应额度池的 5h 和周限剩余百分比、重置倒计时、上下文占用；TPS 从 transcript_path 指向的会话日志里按最近一轮输出计算。配进 ~/.gemini/antigravity-cli/settings.json，开启 stack_with_default，保留默认状态栏。
```

───

# 四、出片：Flow 点数省着花，Colab 算力别浪费

生图：agy 内置生图选不了模型。

agy 自带的生图工具只收提示词、文件名和画幅，用哪个模型由服务端按账号分配，你指定不了。想锁定 Nano Banana Pro，只能去 Flow 网页里选，或者走 API。

同一批提示词，我让 agy 内置生图和 Flow 的 Nano Banana Pro 各出了一组对比。我做的是写实的巨型建筑，最后反而觉得 agy 的更好一些。

Flow：生图不扣点，点数都花在视频上。

我用 Pro 账号在 Flow 里实测，单条 x1：

- Nano Banana 2.1、Nano Banana Pro 生图：0 点；
- Veo 3.1 Lite 视频：10 点；
- Veo 3.1 Fast 视频（720p、8 秒）：20 点；
- Omni 1.2 Flash（720p、8 秒）：24 点。

[图：Flow 模型下拉和点数]

这一步注意：我做的时候，Flow 面板提示 Veo 3.1 Fast 和 Quality 将在 12 月 5 日停用，用之前看一眼面板。

Colab：最容易被忽略的权益。

Ultra 送了 Colab 算力，我这个号有 2500 个算力单元。开一台 G4（RTX PRO 6000 Blackwell，96G 显存），用 ComfyUI 跑开源的 MiniMax H3 图生视频：

- 5 条 768×1344 竖屏视频，从开机、拉模型、启动 ComfyUI 到全部下载回来，大约 11 分钟，一共 1.83 个算力单元；
- 机器热着连续跑，每条大约 80 秒；
- 后来一批 18 条，花了 14.65 个算力单元。

我踩过这个坑：Colab 开着不用也计费，跑完一定马上停机。

怎么确认生效了：停机后跑 colab usage，看到 Active assignments: 0 才算真停了。

画质怎么选：静态大场景，Veo 更稳。

我用 Flow 的 Veo 3.1 和 Colab 的 H3 出同一批镜头，我感觉 Flow 的效果比 H3 好。密集建筑这种静态大场景，Veo 的透视和窗格稳很多。

原因之一是 H3 我一开始用的是剪枝加 INT8 量化、再挂 8 步 Turbo 加速的版本，整套 42GB 左右，容易闪、镜头会飘。满血的 BF16 版本整套约 123.6GB，可以在 G4 上跑，记得把模型放 Google Drive，别每次从 Hugging Face 现拉。

一键指令：

```
用 colab CLI 开一台 G4，按 ComfyUI 部署 MiniMax H3，把 inputs/ 下的首帧图批量生成 9:16 视频。记录每条耗时和算力消耗，全部下载回本地后立刻停机，最后跑 colab usage 确认没有活跃会话，把耗时和消耗写进一份报告。
```

───

# 五、Colab 登录：别用默认那种

colab CLI 默认的登录方式，是在浏览器里授权、再把授权码复制回终端。我有个号授权成功 9 秒以后，token 就被 Google 吊销了，报 invalid_grant。

我一开始连 gcloud 是什么都不知道。它是 Google Cloud 的官方命令行工具，这里只借它的登录功能：

1. 运行 gcloud auth application-default login，走本地回调登录；
2. colab 命令都加上 --auth=adc。

之后就没再出过问题，而且不会改掉 gcloud 原来的默认账号。

怎么确认生效了：colab --auth=adc whoami 能显示你的账号，usage 能查到算力余额。

───

# 六、条款：反代和套壳的红线

这一节最重要。

反代：条款明确禁止。

社区里把 agy 的 OAuth 额度转给别的工具用的方案很多，Magpie、CLIProxyAPI、各种号池中转。Antigravity 条款第 6 条写的是，用第三方软件、工具或服务访问 Antigravity 属于违约，可能导致 Antigravity 和 Gemini CLI 账号被暂停或终止。V2EX 和 linux.do 上都有人自报被封。

套壳：FAQ 写了不支持。

FAQ 里有两句话值得看：

- 点名了 Claude Code、OpenClaw、OpenCode，用 Antigravity 的登录去接这些第三方软件，账号可能被停用；
- agy -p 是给直接写脚本和 CI 用的，把 agy 包进第三方编程 Agent 或应用、自动轮换账号，消费者套餐不支持。

现在挺多人推荐 agy 套壳的玩法，包括让别的 agent 调 agy -p，严格说都在这个范围里。我自己也在这么用，所以写在这里提醒大家，也提醒我自己，主力号谨慎。

第三方工具想用 Gemini，官方推荐的是 Google AI Studio API Key 或 Gemini Enterprise，跟会员分开计费。

官方原文：
https://antigravity.google/terms
https://antigravity.google/docs/faq

开会员：这块我没亲身经验。

只是这一个月在 linux.do 看了不少帖子。低价区的车说封就封，苹果支付会被风控，Pixel 和运营商送的会员有突然没了的，还有人买了不到 20 小时整个号就没了。登录 agy 要验证 Google 账号的手机号，国内号经常发不出短信，提前准备好。

───

# 七、什么活用哪个

- 生图、要指定模型：Flow，选 Nano Banana Pro，不扣点
- 随手出图、写实场景：agy 内置生图
- 批量出视频：Colab 跑 H3，跑完马上停机
- 关键镜头、静态大场景：Flow 的 Veo 3.1
- 日常写代码：agy 的 Orchestrator
- 第三方工具要用 Gemini：AI Studio API Key，别拿会员额度去反代

我的组合：Flow 或 agy 出图，Colab 批量出视频，关键镜头再交给 Veo。

───

## 最后

回头看，开头那次等了十分钟的更新，原因就是一个锁加一次断流的下载，结果全写在一个没人会去看的文件里。这篇里不少坑都是这样，报错看不出原因，找到了改起来并不难。

如果这篇帮你少踩了一个坑，转给刚开会员、正在跟 agy 较劲的朋友。你还踩过什么坑，评论区聊聊。
