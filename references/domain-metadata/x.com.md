---
domain: x.com
aliases: [twitter.com]
type: social-media
visibility: partial
access_stability: dynamic
best_strategy: vxtwitter
---

# x.com (Twitter)

- 类型: 社交媒体
- 可见性: 公开 status 可优先通过 vxTwitter / FixTweet JSON API 读取；部分内容仍需要用户本人浏览器可见，尤其是长线程、投票、私密/受限内容和部分长文类型
- 公开读取稳定性: 动态变化明显，API 限制严格
- 首选方案: `vxtwitter` provider，调用 `api.vxtwitter.com` / `api.fxtwitter.com`，将 tweet JSON 或 X Article `content.blocks` 转为 Markdown
- 替代方案: 若第三方 API 失败，继续使用通用 fallback chain；必要时使用用户可见浏览器或手动复制内容
- 注册方式: 邮箱 / 手机号 / Google / Apple
- 注册页: https://x.com/i/flow/signup
- 注意: vxTwitter / FixTweet 依赖公开页面抓取，Twitter/X 页面结构变化时可能短暂失效；投票、私密内容和特殊长文形态不保证完整
