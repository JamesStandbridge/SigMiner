import json
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
import base64
from PIL import Image
import io


class MultiModalLLM(OpenAIMultiModal):
    def __init__(self, model: str, api_key: str, max_new_tokens: int = 600):
        super().__init__(model=model, api_key=api_key, max_new_tokens=max_new_tokens)

    def query(
        self,
        prompt: str,
        image_bytes: bytes = None,
        mimetype: str = "image/jpeg",
        role: str = "user",
        max_tokens: int = 1000,
        temperature: float = 0.0,
    ) -> str:

        message = {
            "role": role,
            "content": [{"type": "text", "text": prompt}],
        }

        if image_bytes is not None:
            img = Image.open(io.BytesIO(image_bytes))

            # Check if the image has an alpha channel
            if img.mode == "RGBA":
                background = Image.new("RGBA", img.size, (255, 255, 255, 255))
                img = Image.alpha_composite(background, img).convert("RGB")
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                image_bytes = img_byte_arr.getvalue()

            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            message["content"].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mimetype};base64,{encoded_image}",
                    },
                }
            )

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[message],
            # response_format={"type": "json_object"},
            stream=False,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        try:
            response_content = response.choices[0].message.content
            return response_content
        except Exception as e:
            print("Response generation failed:", e)
            return ""
