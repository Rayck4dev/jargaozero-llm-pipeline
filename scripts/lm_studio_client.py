import os

import requests


class LMStudioClient:
    def __init__(self, base_url=None, model_id=None):
        self.base_url = (
            base_url
            or os.environ.get(
                "JARGAOZERO_API_BASE_URL",
                os.environ.get("VITE_API_BASE_URL", "http://localhost:1235/v1"),
            )
        ).rstrip("/")
        self._model_id = model_id or os.environ.get("JARGAOZERO_LLM_MODEL")
        self._session = requests.Session()

    @property
    def model_id(self):
        if self._model_id:
            return self._model_id

        response = self._session.get(f"{self.base_url}/models", timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("A API /models retornou um formato inesperado.")
        models = payload.get("data")
        if not isinstance(models, list) or not models:
            raise RuntimeError(
                "Nenhum modelo foi encontrado no LM Studio. Carregue um modelo "
                "e inicie o servidor local antes de enviar solicitações."
            )
        if not isinstance(models[0], dict) or not models[0].get("id"):
            raise ValueError("A API /models não retornou um identificador de modelo.")

        self._model_id = models[0]["id"]
        return self._model_id

    def chat_completion(
        self, messages, temperature=0.3, max_tokens=300, timeout=300
    ):
        response = self._session.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("A API de chat completions retornou um formato inesperado.")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ValueError("A API de chat completions não retornou escolhas.")
        message = choices[0].get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ValueError("A API de chat completions retornou conteúdo vazio.")
        return content.strip()
