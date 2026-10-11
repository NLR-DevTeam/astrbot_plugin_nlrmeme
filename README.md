# Astrbot NLR MEME
适用于 Astrbot 的 NLR MEME 插件  
能调用 [NLR MEME](meme.nlrdev.top) 的 MEME/梗图  

### 指令
| 指令名称 | 介绍           | 默认权限 |
|:---------|:---------------|:---------|
| meme     | 获取一张meme图 | 全部     |
| upload   | MEME投稿       | 管理员   |

### 配置项

| 名称                   | 介绍                         | 默认值 | 单位   |
|:-----------------------|:-----------------------------|--------|--------|
| Key                    | API Key                      | -      | -      |
| 指令冷却时间           | 使用指令后再次使用的冷却时间 | 30     | 秒     |
| 超时时长               | 调用meme图的时限，超时则报错 | 15     | 秒     |
| 管理员是否不受冷却影响 | 管理员是否不受冷却的影响     | true   | 布尔值 |

API来源：[YanJi](https://github.com/YanJi314)  

### API Key

API Key 申请需要前往 [CAS](https://cas.mtszedu.com/) 申请  
没有填写 API Key 无法使用本插件的功能，请申请API Key

申请流程：`开发人员选项` —— `接口令牌` —— `创造`

完整的 Key **只在创建时显示一次**，形如 zenithapi-1009…5d0d，请立即复制保存。之后列表里只显示前后 4 位。  
每个账户最多 5 个 API Key；Key 被删除、被管理员禁用或轮换后立即失效。  
API Key 每日只有 **100** 次访问，请妥善使用！
访问过快会导致暂时风控！如遇风控请至少等待 **600秒** 后再重试。如被风控后仍反复尝试调用会导致**永久封禁**！

### 投稿

仅接受不超过 10MB 的图片投稿，支持 JPEG、PNG、GIF、BMP、WebP 等常见格式。  
上传成功后进入审核队列，管理员通过后才会加入图库；被拒绝的图片会被删除，接口不返回审核结果。  
每个账户最多同时有 10 张待审核的图片，达到上限后需等待管理员处理。  
服务器会将图片统一转换为 WebP，动图只保留第一帧。

- 管理员发送 `$upload` 并在同一条消息中附上图片，会直接进入投稿处理。
- 只发送 `$upload` 时，请在 30 秒内发送图片；只接收同一会话中发起者的图片。
- 发送文字或其他非图片消息不会重置计时，超过 30 秒自动取消并提示超时。
- 每次处理第一张图片。别名为 `meme投稿`、`投稿`，指令前缀以 AstrBot 的配置为准。

---
如遇问题欢迎提交 Issue  
多次请求失败请检查网络配置，如仍然失败可添加 [QQ群](https://qun.qq.com/universal-share/share?ac=1&authKey=xAwWT7PrEnmYU0UmuBFGkkuBrHWsZQiVc86yVrcw0tPnHxktSCV%2BSLHdokwSq6VI&busi_data=eyJncm91cENvZGUiOiIxODI4NTA3OTUiLCJ0b2tlbiI6IjZqS0FpOGltSzB4Wml2eGNpTHUzZVdBVng1MVZSNTJKNGJVUlFnbVpWZkpmOVZOR1JuV3h0OXJwUjlWb01COFoiLCJ1aW4iOiI0NTA3NTIyNjIifQ%3D%3D&data=4Sg4OHLk5EzcRjJBgC1muU7fGyP_RJB6EptNRNZNjH2UxRUwY1FKEcEmZbgKSK6hnpc-khyQpmB3NGzQoEi8Mw&svctype=4&tempid=h5_group_info)
