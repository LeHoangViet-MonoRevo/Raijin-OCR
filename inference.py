from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import torch
from prompt_generator import Prompt
from model import TechnicalDrawingExtractor
import time
import glob

if __name__ == "__main__":
    img_dirs = glob.glob("./images/*")
    model_name = "Qwen/Qwen2.5-VL-3B-Instruct"
    dtype = torch.bfloat16
    resized_width = 3840
    resized_height = 2160
    attn_implementation = "flash_attention_2"
    device_map = "cuda:1"
    min_pixels = 512 * 28 * 28
    max_pixels = 1536 * 28 * 28
    use_fast = True
    td_extractor = TechnicalDrawingExtractor(
        model_name=model_name,
        dtype=dtype,
        attn_implementation="flash_attention_2",
        device_map=device_map,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
        use_fast=use_fast,
    )

    prompt = Prompt.technical_drawing_extraction_prompt(
        image_path=img_dirs[2],
        resized_width=resized_width,
        resized_height=resized_height,
    )
    
    start_time = time.time()
    result = td_extractor.run(prompt)
    end_time = time.time()
    print(f"Duration: {end_time - start_time}")
    print(f"Result: {result}")

