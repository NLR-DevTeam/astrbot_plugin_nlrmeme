# Astrbot NLR MEME
适用于 Astrbot 的 NLR MEME 插件  
能调用 [NLR MEME](meme.nlrdev.top) 的 MEME/梗图  

### 指令
| 指令名称 | 介绍           |
|:---------|:---------------|
| meme     | 获取一张meme图 |

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

---
如遇问题欢迎提交 Issue  
多次请求失败请检查网络配置，如仍然失败可添加 [QQ群](https://qun.qq.com/universal-share/share?ac=1&authKey=xAwWT7PrEnmYU0UmuBFGkkuBrHWsZQiVc86yVrcw0tPnHxktSCV%2BSLHdokwSq6VI&busi_data=eyJncm91cENvZGUiOiIxODI4NTA3OTUiLCJ0b2tlbiI6IjZqS0FpOGltSzB4Wml2eGNpTHUzZVdBVng1MVZSNTJKNGJVUlFnbVpWZkpmOVZOR1JuV3h0OXJwUjlWb01COFoiLCJ1aW4iOiI0NTA3NTIyNjIifQ%3D%3D&data=4Sg4OHLk5EzcRjJBgC1muU7fGyP_RJB6EptNRNZNjH2UxRUwY1FKEcEmZbgKSK6hnpc-khyQpmB3NGzQoEi8Mw&svctype=4&tempid=h5_group_info)