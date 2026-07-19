# EnglishPod 单词手册

每天早上 7 点自动往微信推送一条提醒，点开链接就能学。

## 内容
- 179 期 EnglishPod 主持人对话关键单词
- 1658 个词条，按编号倒序（EP222 → EP001 → TJI038）
- 每条含：音标、词性、中文释义、对话原句例句

## 配置步骤

### 1. 注册 GitHub 账号
访问 https://github.com/signup ，注册一个免费账号。

### 2. 用 GitHub 登录 Server酱
访问 https://sct.ftqq.com/ ，点「GitHub 登录」授权。
登录后在「Key&API」页面复制你的 **SENDKEY**。

### 3. 把这个仓库推到你的 GitHub
（可由助手代劳，或手动上传文件）

### 4. 配置 SENDKEY
在 GitHub 仓库：Settings → Secrets and variables → Actions → New repository secret
- Name: `SENDKEY`
- Value: 第 2 步复制的 SENDKEY

### 5. 开启 GitHub Pages
在 GitHub 仓库：Settings → Pages → Source 选 `main` 分支 → Save
等待 1-2 分钟，会生成在线链接：`https://你的用户名.github.io/仓库名/`

### 6. 测试
在仓库 Actions 标签页，找到「每日 EnglishPod 单词提醒」→ Run workflow → 手动触发一次。
微信应该会收到一条提醒消息。

## 说明
- 定时任务每天北京时间 7:00 自动触发（GitHub Actions cron 有几分钟延迟属正常）
- 完全云端运行，电脑关机也不影响
- GitHub Actions 和 Pages 个人用户免费额度足够
- Server酱免费版每天 5 条推送，每天 1 条绰绰有余
