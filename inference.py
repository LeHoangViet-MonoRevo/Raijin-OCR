from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import torch
from prompt_generator import Prompt
from model import TechnicalDrawingExtractor
import time
import glob
from tqdm import tqdm

if __name__ == "__main__":
    img_dirs = glob.glob("./images/*")
    model_name = "Qwen/Qwen2.5-VL-3B-Instruct-AWQ"
    dtype = torch.float16
    attn_implementation = "flash_attention_2"
    device_map = "cuda:1"
    min_pixels = 512 * 28 * 28
    max_pixels = 1536 * 28 * 28
    use_fast = True

    td_extractor = TechnicalDrawingExtractor(
        model_name=model_name,
        dtype=dtype,
        attn_implementation=attn_implementation,
        device_map=device_map,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
        use_fast=use_fast,
    )

    output_txt_path = "extraction_results_3B_AWQ.txt"

    with open(output_txt_path, "w", encoding="utf-8") as f:
        for img_dir in tqdm(img_dirs):
            print(f"Image path: {img_dir}")
            resized_width, resized_height = td_extractor.get_image_dimension(img_dir)
            print(f"Original image size: {resized_width} x {resized_height}")
            prompt = Prompt.technical_drawing_extraction_prompt(
                image_path=img_dir,
                resized_width=resized_width * 2,
                resized_height=resized_height * 2,
            )

            start_time = time.time()
            response = td_extractor.run(prompt)
            end_time = time.time()

            print(f"Raw_response: {response}\n")
            print(f"Time taken: {end_time - start_time:.2f} seconds\n")

            # Save to txt file
            f.write(f"Image path: {img_dir}\n")
            f.write(f"Response:\n{response}\n")
            f.write(f"Time taken: {end_time - start_time:.2f} seconds\n")
            f.write("=" * 80 + "\n")
