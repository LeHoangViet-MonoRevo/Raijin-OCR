import json
import re


class OCRPostProcessor:
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

    DISALLOWED_VALUES = {
        "none",
        "none of the above",
        "[value]",
        "[none]",
        "[text]",
        "[code]",
        "code",
        "value",
        "text",
        "name",
        "type",
        "material",
        "なし",
    }

    def __init__(self):
        pass

    def clean_value(self, val, key=None):
        if not val:
            return ""

        val = val.strip()
        val_lower = val.lower()
        key_lower = key.lower() if key else ""

        if val_lower == key_lower or val_lower in self.DISALLOWED_VALUES:
            return ""

        if key in self.EXPECTED_VALUES:
            for expected in self.EXPECTED_VALUES[key]:
                if val_lower == expected.lower():
                    return expected
            return ""

        return val

    def get_instruction_and_content(self, value, key=None):
        value = self.clean_value(value, key)
        return {
            "instruction": "NO" if value == "" else "YES",
            "content": value,
        }

    def clean_dimension(self, value):
        if not value:
            return ""

        value = value.replace("×", "x").replace(" ", "").strip()

        if value.startswith("⌀"):
            parts = value[1:].split("x")
            if len(parts) == 2:
                try:
                    float(parts[0])
                    float(parts[1])
                    return f"⌀{parts[0]}x{parts[1]}"
                except ValueError:
                    return ""

        if "x⌀" in value:
            parts = value.split("x⌀")
            if len(parts) == 2:
                try:
                    float(parts[0])
                    float(parts[1])
                    return f"{parts[0]}x⌀{parts[1]}"
                except ValueError:
                    return ""

        parts = value.split("x")
        if len(parts) == 3 and all("⌀" not in p for p in parts):
            try:
                float(parts[0])
                float(parts[1])
                float(parts[2])
                return "x".join(parts)
            except ValueError:
                return ""

        return ""

    def convert_to_output_format(self, entry):
        return {
            "ocr_product_code": self.clean_value(
                entry.get("Product code", ""), "Product code"
            ),
            "ocr_product_name": self.clean_value(
                entry.get("Product name", ""), "Product name"
            ),
            "ocr_drawing_number": self.clean_value(
                entry.get("Product code", ""), "Product code"
            ),
            "ocr_drawing_issuer": self.clean_value(
                entry.get("Customer", ""), "Customer"
            ),
            "material_type": {
                "material_code": self.clean_value(
                    entry.get("Material code", ""), "Material code"
                ),
                "material_type": self.clean_value(
                    entry.get("Material type", ""), "Material type"
                ),
            },
            "required_precision": {
                "tolerance_grade": self.clean_value(
                    entry.get("Tolerance grade", ""), "Tolerance grade"
                ),
                "dimensional_tolerance": self.clean_value(
                    entry.get("Dimensional tolerance", "")
                ),
            },
            "product_shape": {
                "shape": self.clean_value(
                    entry.get("Shape of object", ""), "Shape of object"
                )
                or "others",
                "dimension": self.clean_dimension(entry.get("Dimension of object", "")),
            },
            "surface_roughness": self.clean_value(
                entry.get("Surface roughness", ""), "Surface roughness"
            ),
            "polishing": self.clean_value(entry.get("Polishing", ""), "Polishing"),
            "surface_treatment": self.get_instruction_and_content(
                entry.get("Surface treatment", ""), "Surface treatment"
            ),
            "heat_treatment": self.get_instruction_and_content(
                entry.get("Heat treatment", ""), "Heat treatment"
            ),
            "painting": (
                "NO"
                if self.clean_value(entry.get("Painting", ""), "Painting").lower()
                in ["", "no"]
                else "YES"
            ),
        }

    def parse_model_output(self, text):
        outputs = []
        blocks = text.split("=" * 80)

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

            formatted = self.convert_to_output_format(entry)
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
                "Dimension of object": "10x⌀18",
                "Tolerance grade": "Medium grade",
                "Dimensional tolerance": "±0.1",
                "Polishing": "Yes",
                "Painting": "Yes",
                "Surface roughness": "3.2"
                }
                ```
    """
    processor = OCRPostProcessor()
    parsed_output = processor.parse_model_output(raw_output)
    print(json.dumps(parsed_output[0], indent=2, ensure_ascii=False))
