import json
import re


def clean_value(val):
    val = val.strip()
    return (
        "" if val.lower() in ["none", "none of the above", "[value]", "[none]"] else val
    )


def get_instruction_and_content(value):
    value = clean_value(value)
    return {
        "instruction": "NO" if value == "" else "YES",
        "content": value,
    }


def convert_to_output_format(entry: dict) -> dict:
    return {
        "ocr_product_code": clean_value(entry.get("Product code", "")),
        "ocr_product_name": clean_value(entry.get("Product name", "")),
        "ocr_drawing_number": clean_value(entry.get("Product code", "")),
        "ocr_drawing_issuer": clean_value(entry.get("Customer", "")),
        "material_type": {
            "material_code": clean_value(entry.get("Material code", "")),
            "material_type": clean_value(entry.get("Material type", "")),
        },
        "required_precision": {
            "tolerance_grade": clean_value(entry.get("Tolerance grade", "")),
            "dimensional_tolerance": clean_value(
                entry.get("Dimensional tolerance", "")
            ),
        },
        "product_shape": {
            "shape": clean_value(entry.get("Shape of object", "OTHERS")),
            "dimension": clean_value(entry.get("Dimension of object", "0x0x0"))
            .replace("×", "x")
            .replace(" ", ""),
        },
        "surface_roughness": clean_value(entry.get("Surface roughness", "")),
        "polishing": clean_value(entry.get("Polishing", "")),
        "surface_treatment": get_instruction_and_content(
            entry.get("Surface treatment", "")
        ),
        "heat_treatment": get_instruction_and_content(entry.get("Heat treatment", "")),
        "painting": (
            "NO"
            if clean_value(entry.get("Painting", "")).lower() in ["", "no"]
            else "YES"
        ),
    }


def parse_model_output(text: str) -> list:
    outputs = []
    blocks = text.split(
        "================================================================================"
    )

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        entry = {}
        image_match = re.search(r"Image path:\s*(.*)", block)
        image_path = image_match.group(1).strip() if image_match else ""

        # Try to extract JSON if present
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", block, re.DOTALL)
        if json_match:
            try:
                entry = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                continue  # skip broken json blocks
        else:
            # Fallback to key-value line parsing
            for line in block.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    entry[key.strip()] = value.strip()

        formatted = convert_to_output_format(entry)
        outputs.append({"image_path": image_path, "data": formatted})

    return outputs


if __name__ == "__main__":
    raw_output = """
                ```json
                {
                "Product name": "051AGRA-50A",
                "Product code": "051AGRA-50A",
                "Material code": "SUS304",
                "Material type": "stainless steel",
                "Customer": "SHIMANO REEL SEC.",
                "Heat treatment": "normalizing",
                "Surface treatment": "None of the above",
                "Shape of object": "round",
                "Dimension of object": "⌀30x150",
                "Tolerance grade": "Medium grade",
                "Dimensional tolerance": "±0.1",
                "Polishing": "Yes",
                "Painting": "Yes",
                "Surface roughness": "3.2"
                }
                ```
                 """
    parsed_output = parse_model_output(raw_output)
    print(f"\n {parsed_output[0]['data']}")
