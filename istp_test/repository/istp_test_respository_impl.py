import os

import httpx
import openai

from istp_test.repository.istp_test_repository import IstpTestRepository
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

openaiApiKey = os.getenv('OPENAI_API_KEY')
if not openaiApiKey:
    raise ValueError('API Key가 준비되어 있지 않습니다.')

# fine-tuned model ID
model_istp = os.getenv('ISTP_TEST')

class IstpTestRepositoryImpl(IstpTestRepository):
    __instance = None
    client = OpenAI()

    headers = {
        'Authorization': f'Bearer {openaiApiKey}',
        'Content-Type': 'application/json',
    }

    OPENAI_CHAT_COMPLETIONS_URL= "https://api.openai.com/v1/chat/completions"

    conversation_history = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = cls()

        return cls.__instance

    async def generateText(self, userSendMessage):

        # 사용자 메시지를 대화 히스토리에 추가
        self.conversation_history.append({"role": "user", "content": userSendMessage})

        data = {
            'model': model_istp,
            'messages': self.conversation_history,
            'max_tokens': 256,
            'temperature': 1.0,
        }

        # api에 추론 요청을 보내는 부분
        async with httpx.AsyncClient(timeout=10000) as client:
            try:
                # 우리가 service, repository에서 처리했던 부분을 여기서 딸깍으로 처리해버림
                response = await client.post(self.OPENAI_CHAT_COMPLETIONS_URL, headers=self.headers, json=data)
                response.raise_for_status()

                generatedText = response.json()['choices'][0]['message']['content'].strip()

                # AI의 응답을 대화 히스토리에 추가
                self.conversation_history.append({"role": "assistant", "content": generatedText})

                return { "generatedText": generatedText } # dict 형식으로 반환해주어야 함

            except httpx.HTTPStatusError as e:
                print(f"HTTP Error: {str(e)}")
                print(f"Status Code: {e.response.status_code}")
                print(f"Response Text: {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"HTTP Error: {e}")

            except (httpx.RequestError, ValueError) as e:
                print(f"Request Error: {e}")
                raise HTTPException(status_code=500, detail=f"Request Error: {e}")
