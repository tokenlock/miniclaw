import os
from openai import OpenAI

class OpenAIChat:
    def __init__(
        self,
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        model="google-ai-studio/gemini-3.1-flash-lite-preview",
        max_prompt_tokens=2500
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url  
        )
        self.model = model
        self.messages = []
        self.max_prompt_tokens = max_prompt_tokens

    def add_system_prompt(self, prompt: str):
        """设置系统角色（可选）"""
        self.messages.insert(0, {"role": "system", "content": prompt})

    def chat(self, user_input: str) -> str:
        """发送消息并返回 AI 回答（自动记忆上下文）"""

        # 添加用户消息
        self.messages.append({"role": "user", "content": user_input})
        
        # 请求 OpenAI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            # 获取回答
            answer = response.choices[0].message.content.strip()
            prompt_tokens = response.usage.prompt_tokens
            if prompt_tokens > self.max_prompt_tokens:
                self.trim_context() 

            # 保存 AI 回答到上下文
            self.messages.append({"role": "assistant", "content": answer})
        
        except Exception as e:
            # 统一提取所有模型返回的错误信息
            error_msg = f"⚠️ LLM 服务异常: {str(e)}"
            answer = error_msg
            self.messages.pop() # pop user_input 重新提问
        
        return answer

    def trim_context(self):
        system = [m for m in self.messages if m["role"] == "system"]
        chats = [m for m in self.messages if m["role"] != "system"]
        chats = chats[len(chats) // 2:] # 保留后半段
        self.messages = system + chats

    def reset(self):
        """清空对话记忆"""
        self.messages = []

if __name__ == "__main__":
    llm = OpenAIChat()

    # 3. 对话
    while True:
        user_msg = input("user：")
        if user_msg in ["exit", "quit"]:
            break

        reply = llm.chat(user_msg)
        print("AI：", reply)