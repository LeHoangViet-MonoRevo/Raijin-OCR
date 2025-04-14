import json
import re

EXPECTED_VALUES = {
    "Material type": [
        "stainless steel",
        "iron",
        "aluminum",
        "casting",
        "brass",
        "copper",
    ],
    "Heat treatment": [
        "quenching",
        "high-frequency quenching",
        "tempering",
        "normalizing",
        "carburizing",
        "vacuum heat treatment",
    ],
    "Surface treatment": [
        "anodizing",
        "non-electrolytic plating",
        "black dyeing or blackening",
        "phosphate manganese coating",
        "trivalent chromate (ZMC3)",
        "hard chrome plating",
    ],
    "Shape of object": ["round", "angle", "plate", "others"],
    "Tolerance grade": [
        "Fine grade",
        "Medium grade",
        "Coarse grade",
        "Very coarse grade",
        "Not selected",
    ],
    "Surface roughness": ["G", "0.8", "1.6", "3.2", "Ra12.5"],
    "Polishing": ["Yes", "No"],
    "Painting": ["Yes", "No"],
}


def clean_value(val, key=None):
    if not val:
        return ""
    val = val.strip()

    # Ignore placeholder values
    if val.lower() in ["none", "none of the above", "[value]", "[none]"]:
        return ""

    # Prevent key = value hallucination
    if key and val.lower() == key.lower():
        return ""

    # Check for expected categories if key is provided
    if key in EXPECTED_VALUES:
        # Handle fuzzy matching like Ra12.5 for surface roughness
        for expected in EXPECTED_VALUES[key]:
            if val.lower() == expected.lower():
                return expected
        return ""

    return val


def get_instruction_and_content(value, key=None):
    value = clean_value(value, key)
    return {
        "instruction": "NO" if value == "" else "YES",
        "content": value,
    }


def convert_to_output_format(entry: dict) -> dict:
    return {
        "ocr_product_code": clean_value(entry.get("Product code", ""), "Product code"),
        "ocr_product_name": clean_value(entry.get("Product name", ""), "Product name"),
        "ocr_drawing_number": clean_value(
            entry.get("Product code", ""), "Product code"
        ),
        "ocr_drawing_issuer": clean_value(entry.get("Customer", ""), "Customer"),
        "material_type": {
            "material_code": clean_value(
                entry.get("Material code", ""), "Material code"
            ),
            "material_type": clean_value(
                entry.get("Material type", ""), "Material type"
            ),
        },
        "required_precision": {
            "tolerance_grade": clean_value(
                entry.get("Tolerance grade", ""), "Tolerance grade"
            ),
            "dimensional_tolerance": clean_value(
                entry.get("Dimensional tolerance", "")
            ),
        },
        "product_shape": {
            "shape": clean_value(entry.get("Shape of object", ""), "Shape of object")
            or "others",
            "dimension": clean_value(
                entry.get("Dimension of object", ""), "Dimension of object"
            )
            .replace("×", "x")
            .replace(" ", ""),
        },
        "surface_roughness": clean_value(
            entry.get("Surface roughness", ""), "Surface roughness"
        ),
        "polishing": clean_value(entry.get("Polishing", ""), "Polishing"),
        "surface_treatment": get_instruction_and_content(
            entry.get("Surface treatment", ""), "Surface treatment"
        ),
        "heat_treatment": get_instruction_and_content(
            entry.get("Heat treatment", ""), "Heat treatment"
        ),
        "painting": (
            "NO"
            if clean_value(entry.get("Painting", ""), "Painting").lower() in ["", "no"]
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

        json_match = re.search(r"```json\s*(\{.*?\})\s*```", block, re.DOTALL)
        if json_match:
            try:
                entry = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                continue
        else:
            for line in block.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    entry[key.strip()] = value.strip()

        formatted = convert_to_output_format(entry)
        outputs.append(formatted)

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
    print(json.dumps(parsed_output[0], indent=2, ensure_ascii=False))
