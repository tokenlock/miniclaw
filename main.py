import os
import asyncio
from bot import WechatAsyncBot
from chat import OpenAIChat

class WechatAIBot:
    def __init__(self):
        self.wechat = WechatAsyncBot()
        self.llm = OpenAIChat(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model="google-ai-studio/gemini-3.1-flash-lite-preview"
        )

        self.commands = {}
        self.register_commands()

    def register_commands(self):
        self.register_command("/reset", self.cmd_reset)
        self.register_command("/clear", self.cmd_reset)
        self.register_command("/help",  self.cmd_help)

    def register_command(self, cmd: str, func):
        self.commands[cmd.lower()] = func

    def cmd_reset(self, cmd, args):
        self.llm.reset()
        return "🔄 reset success"

    def cmd_help(self, cmd, args):
        lines = []
        lines.append("📜 可用命令：")
        lines.append("/reset    - 重置对话")
        lines.append("/help     - 显示帮助")
        return "\n".join(lines)

    def run_command(self, text: str):
        text = text.strip()
        if not text.startswith("/"):
            return None

        parts = text.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in self.commands:
            return self.commands[cmd](cmd, args)
        return None

    async def session_loop(self):
        while True:
            if self.wechat.user_texts:
                text, ctx = self.wechat.user_texts.pop(0)
                user_input = text.strip()

                reply = self.run_command(user_input)
                if reply is None:
                    # ======================================
                    # 🔥 开始思考 → 显示「对方正在输入」
                    # ======================================
                    await self.wechat.send_typing(
                                context_token=ctx,
                                status=1
                    )
                    reply = self.llm.chat(user_input)

                await self.wechat.send(reply, ctx)
                # ======================================
                # ✅ 思考完成 → 取消输入状态 斜杠命令不思考直接status 2
                # ======================================
                await self.wechat.send_typing(
                    context_token=ctx,
                    status=2
                )

            await asyncio.sleep(0.5)

    async def run(self):
        await self.wechat.start()
        asyncio.create_task(self.wechat.listen())
        asyncio.create_task(self.session_loop())
        await asyncio.Event().wait()


if __name__ == "__main__":
    bot = WechatAIBot()
    asyncio.run(bot.run())