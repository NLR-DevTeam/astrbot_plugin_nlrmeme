import asyncio
import mimetypes
import time
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, cast
import httpx
import math
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    SessionController,
    SessionFilter,
    session_waiter,
)

plugin_dir = Path(__file__).parent
error_img = str(plugin_dir / "resource" / "error_img.jpg")


class UploadSessionFilter(SessionFilter):
    def filter(self, event: AstrMessageEvent) -> str:
        # 群聊中也只接收发起投稿的用户，避免其他人的图片被误投稿。
        return f"nlrmeme-upload:{event.unified_msg_origin}:{event.get_sender_id()}"


@register("NLRMeme", "aipiao_", "调用 NLR MEME/梗图插件", "1.2.0")
class NLRMeme(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self._upload_tasks: dict[str, asyncio.Task] = {}

    cooldowns: dict[str, float] = {}

    def cold_check(self, event: AstrMessageEvent, sender_id: str, cold_time: int):
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
            ok, remain = self.cold_check(event, sender_id, self.config.time)
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

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("upload", alias={"meme投稿", "投稿"})
    async def upload_meme(self, event: AstrMessageEvent):
        """仅接受图片；未附图时等待同一用户在 30 秒内发送图片。"""
        session_filter = UploadSessionFilter()
        session_id = session_filter.filter(event)
        if session_id in self._upload_tasks:
            yield event.plain_result("你已有一个等待中的投稿，请发送图片")
            return

        images = [item for item in event.get_messages() if isinstance(item, Comp.Image)]
        if images:
            yield self._upload_result(event, await self._submit_meme_image(event, images[0]))
            return

        received_image: Comp.Image | None = None
        received_event: AstrMessageEvent | None = None
        deadline = time.monotonic() + 30

        async def wait_for_image(controller: SessionController, next_event: AstrMessageEvent) -> None:
            nonlocal received_image, received_event
            if time.monotonic() >= deadline:
                controller.stop(TimeoutError("等待图片超时"))
                return
            next_images = [
                item for item in next_event.get_messages() if isinstance(item, Comp.Image)
            ]
            if not next_images:
                await next_event.send(next_event.plain_result("只接受图片投稿，请在剩余时间内发送图片。"))
                # 不重置计时：始终从最初的 upload 指令起计算 30 秒。
                return
            received_image = next_images[0]
            received_event = next_event
            controller.stop()

        # 装饰器会把回调签名 (controller, event) 转成 (event, session_filter)。
        # 显式声明装饰后的签名，避免编辑器沿用原回调签名检查参数。
        wait_for_image_session = cast(
            Callable[[AstrMessageEvent, SessionFilter], Coroutine[Any, Any, None]],
            session_waiter(timeout=30)(wait_for_image),
        )
        task = asyncio.create_task(wait_for_image_session(event, session_filter))
        self._upload_tasks[session_id] = task
        try:
            yield event.plain_result("请在 30 秒内发送要投稿的图片")
            await task
            if received_image is not None and received_event is not None:
                yield self._upload_result(event, await self._submit_meme_image(received_event, received_image))
        except TimeoutError:
            yield event.plain_result("发送超时！30 秒内未收到图片，投稿已取消。")
        finally:
            self._upload_tasks.pop(session_id, None)
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    def _upload_result(self, event: AstrMessageEvent, message: str | None):
        if message is None:
            return event.chain_result([
                Comp.Plain("投稿失败"),
                Comp.Image.fromFileSystem(error_img),
            ])
        return event.plain_result(message)

    async def _submit_meme_image(self, event: AstrMessageEvent, image: Comp.Image) -> str | None:
        api_key = (self.config.key or "").strip()
        if not api_key:
            logger.warning("API Key有误！请检查API Key后重新投稿")
            return "请先在插件配置中填写 API Key，再进行投稿。"

        max_size = 10 * 1024 * 1024
        try:
            image_path = Path(await asyncio.wait_for(
                image.convert_to_file_path(), timeout=float(self.config.timeout or 15)
            ))

            def read_image():
                # 限制读取量，避免将超大图片整个载入内存。
                with image_path.open("rb") as file:
                    return file.read(max_size + 1)

            content = await asyncio.to_thread(read_image)
            if len(content) > max_size:
                return "投稿失败：图片不能超过 10MB。"
            if not content:
                return "投稿失败：图片文件为空，请重新发送图片。"

            content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
            response = await self._client.post(
                "https://moonlight.api.mtszedu.com/moonlight/meme/upload",
                headers={"Authorization": api_key},
                files={"image": (image_path.name, content, content_type)},
            )
            if response.status_code == 429:
                return "请求太快啦！请等待 10 分钟后再尝试投稿。"
            if response.status_code == 413:
                return "投稿失败：图片不能超过 10MB。"

            # 错误响应也可能带有业务 code，先解析再处理 HTTP 状态，
            # 避免 HTTP 400 直接跳过 Key 无效等具体提示。
            try:
                result = response.json()
            except ValueError:
                response.raise_for_status()
                return "投稿失败：服务器返回了无效的响应，请稍后重试。"

            code = result.get("code") if isinstance(result, dict) else None
            errors = {
                -1: "Key 无效或已禁用！请检查 API Key。",
                -2: "待审核图片已达 10 张，请等待管理员审核后再投稿。",
                -3: "投稿失败：文件不是可识别的图片，或超过 10MB。",
                -4: "服务器保存图片失败，请稍后重试。",
            }
            if type(code) is int and code in errors:
                return errors[code]
            if type(code) is not int or code != 0:
                logger.error(
                    "投稿接口返回未知状态码：code=%r，HTTP=%s，响应=%r",
                    code, response.status_code, result,
                )
                # None 表示使用统一错误图片回复，详细原因只记录到日志。
                return None
            response.raise_for_status()
            return "投稿成功！图片已进入审核队列，管理员通过后才会加入图库。"
        except (httpx.TimeoutException, TimeoutError):
            return "图片获取或上传超时，无法确认投稿是否成功，请稍后检查再重试。"
        except httpx.HTTPStatusError as exc:
            logger.error("投稿接口 HTTP 错误：%s", exc.response.status_code)
            return f"投稿失败：服务器返回 HTTP {exc.response.status_code}，请稍后重试。"
        except Exception as exc:
            logger.error("图片投稿失败：%s", exc)
            return "图片获取或上传失败，请检查网络或重新发送图片。"

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        upload_tasks = list(self._upload_tasks.values())
        for task in upload_tasks:
            task.cancel()
        await asyncio.gather(*upload_tasks, return_exceptions=True)
        self._upload_tasks.clear()
        if getattr(self, "_client", None):
            await self._client.aclose()
        self.cooldowns.clear()
        logger.info('NLR MEME 已卸载！')
