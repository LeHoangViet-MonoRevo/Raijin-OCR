from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import torch
from PIL import Image
import numpy as np
from typing import Union
from post_processing import OCRPostProcessor


class TechnicalDrawingExtractor:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-VL-3B-Instruct",
        dtype: torch.dtype = torch.bfloat16,
        attn_implementation: str = "flash_attention_2",
        device_map: str = "auto",
        min_pixels: int = 512 * 28 * 28,
        max_pixels: int = 1536 * 28 * 28,
        use_fast: bool = True,
    ) -> None:

        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=dtype,
            attn_implementation=attn_implementation,
            device_map=device_map,
        )

        self.processor = AutoProcessor.from_pretrained(
            model_name,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
            use_fast=use_fast,
        )

        self.model_parser = OCRPostProcessor()

    @staticmethod
    def get_image_dimension(image_path: Union[str, np.ndarray]) -> tuple[int, int]:
        """
        Get the dimensions of the image.
        :param image_path: Path to the image file or numpy array of the image.
        :return: Tuple containing width and height of the image.
        """
        if isinstance(image_path, str):
            with Image.open(image_path) as img:
                width, height = img.size
        else:
            height, width = image_path.shape[:2]

        return width, height

    def run(self, prompt: list[dict], max_new_tokens: int = 512) -> str:

        # Step 1: Prepare input for model
        text = self.processor.apply_chat_template(
            prompt, tokenize=False, add_generation_prompt=True
        )

        image_inputs, _ = process_vision_info(prompt)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=None,
            padding=True,
            return_tensors="pt",
        ).to(self.model.device)

        # Step 2: Generate response
        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)

        generated_ids_trimmed = [
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization=False
        )

        if output_text:
            response = self.model_parser.parse_model_output(output_text[0])
        else:
            response = ""
        return response
