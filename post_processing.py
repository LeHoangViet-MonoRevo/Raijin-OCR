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
        "Shape of object": ["round", "angle", "plate", "others"],
        "Tolerance grade": [
            "Fine grade",
            "Medium grade",
            "Coarse grade",
            "Very coarse grade",
            "Not selected",
        ],
        "Surface roughness": [
            "Ra0.4",
            "Ra0.8",
            "Ra1.6",
            "Ra3.2",
            "Ra6.3",
            "Ra12.5",
            "Ra25~",
        ],
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
        "null",
        "not exist",
        "not exist in the drawing",
    }

    def __init__(self):
        pass

    def strip_wrappers(self, val):
        try:
            return re.sub(r"^[\[\(\{\"\']+|[\]\)\}\"\']+$", "", val.strip())
        except Exception:
            return ""

    def clean_value(self, val, key=None):
        try:
            if not val:
                return ""
            val = self.strip_wrappers(val)
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
        except Exception:
            return ""

    def get_instruction_and_content(self, value, key=None):
        try:
            # value = self.strip_wrappers(value)
            # value = value.strip()
            value = self.clean_value(value)
            return {
                "instruction": "NO" if value == "" else "YES",
                "content": value,
            }
        except Exception:
            return {"instruction": "NO", "content": ""}

    def convert_phi_to_box(self, value):
        try:
            if not value:
                return ""

            value = value.replace("×", "x").replace(" ", "").strip()
            value = re.sub(r"[\[\]{}()]", "", value)

            if value.startswith("⌀"):
                parts = value[1:].split("x")
                if len(parts) == 2:
                    d = float(parts[0])
                    l = float(parts[1])
                    return f"{d}x{d}x{l}"

            if "x⌀" in value:
                parts = value.split("x⌀")
                if len(parts) == 2:
                    l = float(parts[0])
                    d = float(parts[1])
                    return f"{l}x{d}x{d}"

            return ""
        except Exception:
            return ""

    def clean_dimension(self, value):
        try:
            if not value:
                return ""
            value = self.strip_wrappers(value)
            value = value.replace("×", "x").replace(" ", "").strip()

            phi_box = self.convert_phi_to_box(value)
            if phi_box:
                return phi_box

            parts = value.split("x")
            if len(parts) == 3 and all("⌀" not in p for p in parts):
                float(parts[0])
                float(parts[1])
                float(parts[2])
                return "x".join(parts)
            return ""
        except Exception:
            return ""

    def convert_to_output_format(self, entry):
        try:
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
                    "dimension": self.clean_dimension(
                        entry.get("Dimension of object", "")
                    ),
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
        except Exception:
            return {
                "ocr_product_code": "",
                "ocr_product_name": "",
                "ocr_drawing_number": "",
                "ocr_drawing_issuer": "",
                "material_type": {
                    "material_code": "",
                    "material_type": "",
                },
                "required_precision": {
                    "tolerance_grade": "",
                    "dimensional_tolerance": "",
                },
                "product_shape": {
                    "shape": "others",
                    "dimension": "",
                },
                "surface_roughness": "",
                "polishing": "",
                "surface_treatment": {"instruction": "NO", "content": ""},
                "heat_treatment": {"instruction": "NO", "content": ""},
                "painting": "NO",
            }

    def parse_model_output(self, text):
        outputs = []
        try:
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
        except Exception:
            pass
        return outputs


if __name__ == "__main__":
    raw_output = """
        ```json
        {
        "Product name": "JOINT",
        "Product code": "26015-X1JJ0-A",
        "Material code": "SS400",
        "Material type": "stainless steel",
        "Customer": "TOYOTA BOSHOKU CORPORATION",
        "Heat treatment": "MTB",
        "Surface treatment": "GC",
        "Shape of object": "angle",
        "Dimension of object": "⌀9.32 * 3.17",
        "Tolerance grade": "Medium grade",
        "Dimensional tolerance": "±0.1",
        "Polishing": "Yes",
        "Painting": "Yes",
        "Surface roughness": "Ra0.8"
        }
        ```
    """
    processor = OCRPostProcessor()
    parsed_output = processor.parse_model_output(raw_output)
    print(json.dumps(parsed_output[0], indent=2, ensure_ascii=False))
