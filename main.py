import time
from pathlib import Path
import httpx
import math
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core import AstrBotConfig
import astrbot.api.message_components as Comp

plugin_dir = Path(__file__).parent
error_img = str(plugin_dir / "resource" / "error_img.jpg")

@register("nlrmeme", "aipiao_", "调用 NLR MEME/梗图插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
    cooldowns: dict[str, float] = {}

    def cold_check(self,event: AstrMessageEvent,sender_id:str):
        cold_time = self.config.time
        last_time = self.cooldowns.get(sender_id)
        now = time.time()

        #管理员豁免，可在配置文件开关
        if self.config.admin:
            if event.is_admin():
                return True,0

        #首次调用放行
        if last_time is None:
            self.cooldowns[sender_id] = now
            return True, 0

        #冷却判断
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
    async def helloworld(self, event: AstrMessageEvent):
        """随机获取一个meme"""
        sender_id = event.get_sender_id()
        try:
            ok, remain = self.cold_check(event, sender_id)
        except Exception as e:
            logger.error(e)
        else:
            try:
                if ok:
                    response = await self._client.get(
                        "https://moonlight.api.mtszedu.com/moonlight/meme/index"
                    )
                    response.raise_for_status()
                    json = response.json()
                    data_type = json["data"]["type"]
                    if data_type == 'image':
                        img = json["data"]["content"]
                        yield event.image_result(img)
                    elif data_type == 'text':
                        text = json["data"]["text"]
                        yield event.plain_result(text)
                    else:
                        yield event.plain_result('未知错误！请查看日志！')
                        raise ValueError("未知错误")
                else:
                    yield event.plain_result(f'冷却中！请等待 {math.ceil(remain)} 秒')
            except ValueError as e:
                logger.error(e)
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