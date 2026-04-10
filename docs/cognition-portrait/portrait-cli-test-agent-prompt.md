# Portrait CLI Test Agent Prompt

Use the prompt below when you want to hand the new TopicLab portrait CLI test
task to another agent.

## Ultra-Short Forward Template

```text
请作为 TopicLab Portrait CLI 测试智能体，去验证新的画像主入口是否可用。

先读这份手册：
/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/docs/cognition-portrait/portrait-cli-agent-manual.md

如果本地路径不可用，就读 GitHub preview 版本：
https://github.com/Boyuan-Zheng/Tashan-TopicLab/blob/preview/portrait/docs/cognition-portrait/portrait-cli-agent-manual.md

如需固定源码版本，可优先使用这些 preview 标识：
- Tashan-TopicLab: `tashan-topiclab-portrait-preview-2026.04.11.1`
- TopicLab-CLI: `topiclab-cli-v0.4.0-portrait.1`

然后优先从 GitHub preview 分支下载或进入已有的 TopicLab-CLI 仓库，执行：
npm install
npm run portrait:preview:bootstrap

之后 source bootstrap 生成的 env 文件，用你自己的 staging/test 账号登录 AutoDL staging。

注意：这不是只跑一条命令的测试。你需要把 CLI 当成连续交互入口，连续执行多条命令。

至少完成：
- topiclab portrait start --mode legacy_product
- topiclab portrait respond --choice direct
- topiclab portrait respond --text ...
- topiclab portrait status
- 再继续一次 topiclab portrait respond --text ...
- topiclab portrait result

如果成功，再继续测：
- topiclab portrait resume
- topiclab portrait history
- topiclab portrait export
- topiclab portrait reset

不要默认使用生产账号，也不要优先使用底层调试命令，除非主入口失败。

最后按这个格式汇报：
- clone/install/bootstrap 是否成功
- 登录/注册是否成功
- 成功执行了哪些命令
- 是否证明了可以连续使用 CLI 多轮交互
- 返回了哪些关键结果
- 哪一步失败了（如果失败）
- 你对当前产品可用性的结论
```

## Ready-To-Paste Prompt

```text
你现在是 TopicLab Portrait CLI 测试智能体。

你的目标不是修改产品架构，而是作为使用者去测试新的画像产品主入口是否可用。

请严格按下面要求执行：

1. 先阅读这份操作手册：
   /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/docs/cognition-portrait/portrait-cli-agent-manual.md

2. 使用本地仓库中的独立 TopicLab-CLI checkout：
   如果本地没有，就从 GitHub clone：
   https://github.com/Boyuan-Zheng/TopicLab-CLI
   并切到：
   preview/portrait

   如果本地已经有明确同步过 preview 分支的 checkout，也可以直接使用。

3. 进入上面的独立 TopicLab-CLI 仓库后，优先执行：
   npm install
   npm run portrait:preview:bootstrap

4. 然后 source bootstrap 生成的 env 文件，并使用你自己的 staging 账号登录：
   topiclab portrait auth ensure

   这里把 `auth ensure` 视为“注册或登录”的统一入口，不要自己猜该先注册还是先登录。

5. 你必须把 CLI 当成连续可交互的入口来使用，而不是只跑一条命令。
   也就是说，在同一个本地环境里连续执行多次：
   - start
   - respond
   - status
   - respond
   - result

   如果中途暂停，再回来时应尝试：
   - resume
   - status

6. 至少完成下面这条最小测试闭环：
   - topiclab portrait start --mode legacy_product
   - topiclab portrait respond --choice direct
   - topiclab portrait respond --text ...
   - topiclab portrait status
   - 再继续一次 topiclab portrait respond --text ...
   - topiclab portrait result

7. 如果最小闭环成功，再继续测试：
   - topiclab portrait resume
   - topiclab portrait history
   - topiclab portrait export
   - topiclab portrait reset

8. 不要默认使用生产账号。当前应使用 staging/test 账号。

9. 不要优先使用底层调试命令：
   - topiclab scales ...
   - topiclab portrait dialogue ...
   - topiclab portrait state ...
   除非主入口失败且你需要定位问题。

10. 测试完成后，请按下面格式输出：
   - 是否成功完成 clone/install/bootstrap
   - 是否成功登录或注册
   - 成功执行了哪些命令
   - 是否证明了可以连续使用 CLI 多轮交互
   - 返回了哪些关键结果
   - 哪一步失败了（如果失败）
   - 你对当前产品可用性的结论

补充说明：
- 当前测试目标是云上 AutoDL staging 画像服务
- 目标是验证“本地 CLI -> 云上画像应用”的主入口闭环
- 不需要 SSH 隧道
```

## Suggested Handoff Note

If you want to send a short human note together with the prompt, use:

```text
请按这份 prompt 测试新的 TopicLab 画像 CLI 主入口，优先验证作为普通使用者是否能顺利跑通，而不是先进入底层调试模式。
```
