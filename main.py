import time
from pathlib import Path
import httpx
import math
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig
import astrbot.api.message_components as Comp

plugin_dir = Path(__file__).parent
error_img = str(plugin_dir / "resource" / "error_img.jpg")


@register("NLRMeme", "aipiao_", "调用 NLR MEME/梗图插件", "1.0.2")
class NLRMeme(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    cooldowns: dict[str, float] = {}

    def cold_check(self, event: AstrMessageEvent, sender_id: str):
        cold_time = self.config.time
        last_time = self.cooldowns.get(sender_id)
        now = time.time()

        # 管理员豁免，可在配置文件开关
        if self.config.admin:
            if event.is_admin():
                return True, 0

        # 首次调用放行
        if last_time is None:
            self.cooldowns[sender_id] = now
            return True, 0

        # 冷却判断
        elapsed = now - last_time
        remain = cold_time - elapsed

        if remain <= 0:
            self.cooldowns[sender_id] = now
            return True, 0

        return False, remain

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self._client = httpx.AsyncClient(timeout=float(self.config.timeout or 15))
        logger.info('NLR MEME 加载成功！')

    @filter.command("meme")
    async def get_meme(self, event: AstrMessageEvent):
        """随机获取一个meme"""
        sender_id = event.get_sender_id()
        api_key = self.config.key
        try:
            ok, remain = self.cold_check(event, sender_id)
        except Exception as e:
            logger.error(e)
        else:
            try:
                if ok:
                    url = "https://moonlight.api.mtszedu.com/moonlight/meme/index"
                    header = {
                        "Authorization": api_key
                    }
                    data = {
                        "a": "getMeme"
                    }
                    response = await self._client.post(
                        url=url,
                        headers=header,
                        data=data
                    )
                    if response.status_code == 400:
                        yield event.plain_result(f"Key 无效！请检查API Key的填写是否正确")
                        logger.error('Key 无效！')
                        return
                    elif response.status_code == 429:
                        yield event.plain_result("请求太快啦！休息10分钟吧~")
                        logger.warning("请求过快！请等待10分钟后再重试！")
                    else:
                        response.raise_for_status()
                    json = response.json()
                    logger.info(json)
                    status_code = json["code"]
                    if status_code == 0:
                        data_type = json["data"]["type"]
                        if data_type == 'image':
                            img = json["data"]["content"]
                            yield event.image_result(img)
                        elif data_type == 'text':
                            text = json["data"]["content"]
                            yield event.plain_result(text)
                        else:
                            yield event.plain_result('未知错误！请查看日志！')
                    elif status_code == -1:
                        yield event.plain_result(f"Key 无效！请检查API Key的填写是否正确")
                        logger.error('Key 无效！')
                        return
                    elif status_code == -2:
                        yield event.plain_result(f"今日的调用次数已用尽！")
                        logger.warning('今日调用次数已用尽！')
                        return
                else:
                    yield event.plain_result(f'冷却中！请等待 {math.ceil(remain)} 秒')
            except Exception as e:
                logger.error(e)
                chain = [
                    Comp.Plain('获取失败'),
                    Comp.Image.fromFileSystem(error_img)
                ]
                yield event.chain_result(chain)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        if getattr(self, "_client", None):
            await self._client.aclose()
        self.cooldowns.clear()
        logger.info('NLR MEME 已卸载！')
