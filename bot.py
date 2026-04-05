import os
import json
import uuid
import asyncio
import aiohttp

class WechatAsyncBot:
    def __init__(self):
        self.base_url = os.getenv("WECHAT_BASE_URL")
        self.token = os.getenv("WECHAT_TOKEN")
        self.to_user_id = os.getenv("WECHAT_USER_ID")
        self.session = None
        self.cursor = ""
        self.user_texts = []
        self.headers = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self.token}"
        }
        # 缓存 ticket
        self.typing_ticket_cache = {}

    async def start(self):
        self.session = aiohttp.ClientSession()
        print("✅ 异步机器人已启动")

    # ----------------------
    # 发送消息
    # ----------------------
    async def send(self, text: str, context_token: str = ""):
        payload = {
            "msg": {
                "to_user_id": self.to_user_id,
                "client_id": f"bot-{uuid.uuid4().hex[:12]}",
                "message_type": 2,
                "message_state": 2,
                "context_token": context_token,
                "item_list": [{"type": 1, "text_item": {"text": text}}]
            }
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        try:
            async with self.session.post(
                f"{self.base_url}/ilink/bot/sendmessage",
                data=body,
                headers=self.headers,
                timeout=35
            ) as resp:
                raw = await resp.read()
                raw_data = raw.decode("utf-8")
                data = json.loads(raw_data)
                return data
        except Exception as e:
            print("发送失败:", e)

    async def get_config(self, context_token: str):
        if self.to_user_id in self.typing_ticket_cache:
            return self.typing_ticket_cache[self.to_user_id]

        payload = {
            "ilink_user_id": self.to_user_id,
            "context_token": context_token,
            "base_info": {}  # 官方必须带
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        try:
            async with self.session.post(
                f"{self.base_url}/ilink/bot/getconfig",  # 全小写 ✅
                data=body,
                headers=self.headers,
                timeout=3
            ) as resp:
                raw = await resp.read()
                data = json.loads(raw.decode("utf-8"))
                ticket = data.get("typing_ticket")
                if ticket:
                    self.typing_ticket_cache[self.to_user_id] = ticket
                return ticket

        except Exception as e:
            print("getconfig 错误:", e)
            return None
    # ======================================================================
    # 发送 正在输入 / 取消输入
    # ======================================================================
    async def send_typing(self, context_token: str, status: int = 1):
        ticket = await self.get_config(context_token)
        if not ticket:
            return

        payload = {
            "ilink_user_id": self.to_user_id,
            "typing_ticket": ticket,
            "status": status
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            await self.session.post(
                f"{self.base_url}/ilink/bot/sendtyping",
                data=body,
                headers=self.headers,
                timeout=2
            )
        except:
            pass

    # ----------------------
    # 监听消息
    # ----------------------
    async def listen(self):
        print("🔍 后台消息监听任务已启动")
        while True:
            try:
                payload = {"get_updates_buf": self.cursor}
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                async with self.session.post(
                    f"{self.base_url}/ilink/bot/getupdates",
                    data=body,
                    headers=self.headers,
                    timeout=35
                ) as resp:
                    raw = await resp.read()
                    raw_data = raw.decode("utf-8")
                    data = json.loads(raw_data)

                self.cursor = data.get("get_updates_buf", self.cursor)
                self.user_texts = []

                for msg in data.get("msgs", []):
                    ctx_token = msg.get("context_token", "")
                    for item in msg.get("item_list", []):
                        if item.get("type") == 1:
                            user_text = item.get("text_item", {}).get("text", "")
                            self.user_texts.append([user_text, ctx_token])
                            break

            except Exception as e:
                print("微信监听异常:", e)
                await asyncio.sleep(2)

    # ----------------------
    # 运行入口
    # ----------------------
    async def run(self):
        await self.start()
        asyncio.create_task(self.listen())
        await asyncio.Event().wait()


# ==================== 启动 ====================
if __name__ == "__main__":
    bot = WechatAsyncBot()
    asyncio.run(bot.run())