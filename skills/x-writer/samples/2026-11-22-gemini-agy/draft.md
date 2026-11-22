# Google One 会员 × Antigravity 踩坑记（推文草稿 v2）

> 写法参考：Humanizer-zh 的 31 条模式 + khazix-writer 的禁区（不加粗、不分小标题、少用冒号、不用破折号和双引号、不编亲身经历）。
> 素材：Mac 浏览记录、Mac / dev 容器 / 零刻三台机器的 agy 配置与日志、agy / Claude Code / Codex 会话。数字都是实测记录。
> 已去掉邮箱、主机名、IP、GCP 项目号、公司信息。

---

## 版本 A：长推

用了一个多月 Google One 会员加 Antigravity（下面简称 agy），Mac、Docker 容器、家里那台零刻小主机，三台机器都装了一遍。坑比我想的多，挑几个值得说的记一下。

先说最折磨人的网络。

agy 必须开 Clash 的 TUN 模式，只开系统代理不行。它的模型请求不走 HTTPS_PROXY，会把真实 IP 漏出去，然后报 User location is not supported，官方仓库里也有人提了 issue。后来我干脆在给 agent 的规则里写死，不许它关 Clash，也不许关 TUN，关了它自己也跑不了。

开了 TUN 也不代表万事大吉。前两天 linux.do 突然打不开，我让 agy 去翻 Mihomo 的日志，最后查出来是 DNS 的锅。nameserver 里混着明文的 223.5.5.5，并发查询时它回得最快，拿回来一个被污染的国内 IP，再被排在前面的 GEOIP,CN,DIRECT 判成直连，于是超时。翻历史日志，之前 chat.openai.com 也是这么挂的。

改法是删掉明文 UDP DNS，fallback 换成 IP 形式的 DoH（`https://1.1.1.1/dns-query`），打开 `respect-rules`，再把 GEOIP,CN 挪到 MATCH 前面。

容器里还有个小坑，agy 隔一阵就说我没登录。看日志是刷新 token 的请求 EOF 了，网络断了一下，不是真掉线。先查出口，别急着重登。

然后是 agy 自己。

`agy update` 一直报 update already in progress，我以为卡死了。其实每次启动 agy 都会拉起一个后台更新进程，锁在它手里。安装包 62MB 左右，我这边到 Google 只有一百 KB/s 上下，下到 55MB 断了，校验失败，白等十分钟。结果会写在 `~/.gemini/antigravity-cli/updater/update_status.json`，失败了就按 manifest 里的地址手动下包替换，比反复敲 update 靠谱。

模型我一直用 Orchestrator。它不是一个单独的模型，是强模型先规划、快模型去执行，出了错再切回强模型。日常写代码没必要全程顶配，能省不少额度。

额度在 agy 里敲 `/usage` 看，Gemini 和 Claude/GPT 是两个池子，各有 5 小时限额和周限额。我懒得每次敲，就让 agy 给自己写了个状态栏脚本。statusLine 的 stdin 里本来就有 5h、周限和上下文占用，TPS 没有现成字段，从会话日志里算出来。现在终端底下常驻一行

`5h 97% │ 周限 98% │ Ctx 11% (112k/1M) │ TPS 53 tok/s`

接下来这部分我觉得很多人没用起来，会员给的东西远不止 agy 额度。Flow 能生图生视频，Ultra 档送 Colab 算力，还有 Gemini Notebook。Ultra 附带的 YouTube Premium 是个人版，家庭组成员用不了。

先提醒一句，agy、Flow、Colab CLI 是三套互不相干的登录。我就是 agy 一个号、Flow 一个号、Colab 两个号，有次问 agy 我之前生图用的哪个号，它查了一圈才理清楚。混着用之前，先搞清楚这次扣的是谁的额度。

生图的话，agy 内置的生图工具选不了模型，服务端按账号自动分配。想锁定 Nano Banana Pro，只能去 Flow 网页里选，或者走 API。我的 Pro 账号在 Flow 里用 Nano Banana 生图不扣点数，Veo 3.1 Fast 一条 8 秒 720p 扣 20 点，Lite 扣 10 点，点数基本全花在视频上。同一批提示词，我让 agy 和 Flow（Nano Banana Pro）各出一组对比，我做的是写实的巨型建筑，最后反而更喜欢 agy 出的。

视频的话，Colab 算力很容易被忽略。开一台 G4（RTX PRO 6000，96G 显存），用 ComfyUI 跑开源的 MiniMax H3，5 条竖屏视频从开机、拉模型到下载完，一共花了 1.8 个算力单元。后来连跑 18 条，花了 14.65 个。跑完马上停机，开着不用也计费。

画质上 Veo 3.1 还是稳，尤其是密集建筑这种静态大场景。H3 我先用的是剪枝加 INT8 量化、再挂 8 步 Turbo 的版本，容易闪，镜头会飘。满血 BF16 版权重 120G 出头，放 Google Drive 里，别每次从 Hugging Face 拉。我现在的流程是 Flow 或 agy 出图，Colab 批量出视频，重要的镜头再交给 Veo。

Colab CLI 登录也有坑。默认是复制授权码那种登录，我有个号授权成功 9 秒后 token 就被 Google 吊销了，报 invalid_grant。换成 `gcloud auth application-default login` 走本地回调，再用 `colab --auth=adc`，之后没再出过问题，也不会动 gcloud 原来的默认账号。

最后这条最重要，反代。

社区里把 agy 的 OAuth 额度转给别的工具用的方案很多，Magpie、CLIProxyAPI、各种号池中转。Antigravity 条款第 6 条写得很清楚，用第三方软件访问服务属于违约，可能停掉 Antigravity 和 Gemini CLI 的权限。V2EX 和 linux.do 上都有人自报被封，也有小号反代连坐的说法。

FAQ 里还有两句值得看。一句点名了 Claude Code、OpenClaw、OpenCode，用 Antigravity 的登录接这些第三方工具，账号可能被停用。另一句说 `agy -p` 是给直接写脚本和 CI 用的，把 agy 包进第三方编程 Agent 或应用、自动轮换账号，消费者套餐不支持。现在挺多人推荐的 agy 套壳玩法，严格说都在这个范围里。主力号别冒险，第三方工具想用 Gemini，官方推荐的是 AI Studio API Key 或 Gemini Enterprise，跟会员分开计费。

开会员这块我没什么亲身经验，只是这一个月在 linux.do 看了不少帖子。低价区的车说封就封，苹果支付会被风控，Pixel 和运营商送的会员有突然没了的，还有人买了不到 20 小时整个号就没了。登录 agy 要验证 Google 账号的手机号，国内号经常发不出短信，提前准备好。

暂时就这些。你们还踩过什么坑，评论区说说。

---

## 版本 B：推文串

1/
用了一个多月 Google One 会员加 Antigravity（agy），Mac、Docker 容器、零刻小主机三台都装了一遍，坑比想的多。挑几个值得说的，一条条发。

2/
agy 一定要开 Clash 的 TUN。它的模型请求不走 HTTPS_PROXY，只开系统代理会漏真实 IP，报 User location is not supported。我在 agent 规则里写死了，不许它关 Clash 和 TUN，关了它自己也跑不了。

3/
开了 TUN 也会翻车。前两天 linux.do 打不开，让 agy 翻 Mihomo 日志，是 DNS 的锅。nameserver 混了明文 223.5.5.5，拿回污染的国内 IP，被前面的 GEOIP,CN 判成直连。之前 OpenAI 也是这么挂的。

4/
改法，删掉明文 UDP DNS，fallback 换成 IP 形式的 DoH（1.1.1.1/dns-query），打开 respect-rules，GEOIP,CN 挪到 MATCH 前面。

5/
agy update 老报 update already in progress。其实每次启动都会拉起后台更新进程拿着锁，62MB 的包我这边一百 KB/s，下到一半断了，校验失败。失败原因写在 updater/update_status.json，手动下包替换更快。

6/
模型我一直用 Orchestrator，强模型规划，快模型执行，出错再切回来，比全程顶配省额度。

/usage 看额度，Gemini 和 Claude/GPT 两个池子，各有 5h 限额和周限额。我让 agy 写了个状态栏，常驻一行
5h 97% │ 周限 98% │ TPS 53

7/
会员给的不只 agy 额度，还有 Flow、Colab 算力、Gemini Notebook。

注意 agy、Flow、Colab CLI 是三套独立登录，我在这三处一共登了四个号。用之前先搞清楚扣的是谁的额度。

8/
agy 内置生图选不了模型，想锁 Nano Banana Pro 只能去 Flow 里选。Pro 账号在 Flow 生图不扣点，Veo 3.1 Fast 一条 8 秒扣 20 点，Lite 10 点。同一批提示词对比，我做写实巨构建筑，反而更喜欢 agy 出的。

9/
Ultra 送的 Colab 算力容易被忽略。开一台 G4（RTX PRO 6000 96G）用 ComfyUI 跑开源的 MiniMax H3，5 条竖屏视频连开机带下载 1.8 个算力单元，18 条 14.65 个。跑完马上停机，开着也计费。

10/
画质 Veo 3.1 更稳，量化加 8 步 Turbo 的 H3 容易闪。我现在 Flow 或 agy 出图，Colab 批量出视频，关键镜头上 Veo。

Colab CLI 别用默认的粘贴授权码登录，我一个号 9 秒就被吊销，换 gcloud ADC 加 colab --auth=adc 就好了。

11/
最重要的，别用第三方工具反代 agy 的 OAuth 额度。条款第 6 条写了属于违约，可能停权限，封号帖不少。

FAQ 还点名了 Claude Code、OpenCode，也写了把 agy 包进第三方 Agent、自动轮换账号，消费者套餐不支持。主力号别冒险。

12/
开会员我没亲身经验，只看过帖子。低价区的车说封就封，苹果支付会风控，送的会员有突然没了的。登录要验证手机号，国内号常发不出短信。

还踩过什么坑，评论区聊聊。
