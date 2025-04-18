import json
import re
from typing import Dict, List


class BasePostprocessor:
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

    def strip_wrappers(self, val: str) -> str:
        try:
            return re.sub(r"^[\[\(\{\"\']+|[\]\)\}\"\']+$", "", val.strip())
        except Exception:
            return ""

    def clean_value(self, val, key=None):
        try:
            if not val:
                return ""
            val = self.strip_wrappers(val).strip()
            val_lower = val.lower()
            key_lower = key.lower() if key else ""
            if val_lower == key_lower or val_lower in self.DISALLOWED_VALUES:
                return ""
            return val
        except Exception:
            return ""


class ProductCodePostprocessor(BasePostprocessor):
    def run(self, entry: dict) -> str:
        return self.clean_value(entry.get("Product code", ""), "Product code")


class MaterialTypePostprocessor(BasePostprocessor):
    EXPECTED_VALUES = [
        "stainless steel",
        "iron",
        "aluminum",
        "cast metal",
        "brass",
        "copper",
    ]

    def run(self, entry: dict) -> dict:
        code = self.clean_value(entry.get("Material code", ""), "Material code")
        material = self.clean_value(entry.get("Material type", ""), "Material type")

        if material.lower() in [m.lower() for m in self.EXPECTED_VALUES]:
            return {"material_code": code, "material_type": material}
        return {"material_code": code, "material_type": ""}


class RequiredPrecisionPostprocessor(BasePostprocessor):
    ALLOWED_TOLERANCES = ["±0.001", "±0.01", "±0.1"]

    def get_most_precise_dimensional_tolerance(self, value: str) -> str:
        if not value or "no" in value.lower():
            return "NO_SELECTION"
        has_general_tolerance = "general tolerance" in value.lower()
        value = value.replace(",", " ")
        parts = re.split(r"\s+", value.strip().lower())
        numeric_tolerances = [
            (float(p[1:]), p)
            for p in parts
            if p.startswith("±") and self._is_float(p[1:])
        ]
        if numeric_tolerances:
            numeric_tolerances.sort()
            return numeric_tolerances[0][1]
        if has_general_tolerance:
            return "GENERAL_TOLERANCE"
        return "NO_SELECTION"

    def classify_tolerance(self, value: str) -> str:
        if value == "GENERAL_TOLERANCE":
            return value
        try:
            num = float(value[1:])
            thresholds = sorted((float(t[1:]), t) for t in self.ALLOWED_TOLERANCES)
            for thresh, label in reversed(thresholds):
                if num >= thresh:
                    return label
        except:
            pass
        return "NO_SELECTION"

    def _is_float(self, val):
        try:
            float(val)
            return True
        except ValueError:
            return False

    def run(self, entry: dict) -> dict:
        grade = self.clean_value(entry.get("Tolerance grade", ""), "Tolerance grade")
        raw_tol = entry.get("Dimensional tolerance", "")
        most_precise = self.get_most_precise_dimensional_tolerance(raw_tol)
        category = self.classify_tolerance(most_precise)
        return {
            "tolerance_grade": grade,
            "dimensional_tolerance": category,
        }


class ProductShapePostprocessor(BasePostprocessor):
    def clean_dimension(self, val: str) -> str:
        val = self.clean_value(val, "Dimension of object")
        # You can add specific logic for validating/sanitizing dimension strings here
        return val

    def run(self, entry: dict) -> dict:
        shape = (
            self.clean_value(entry.get("Shape of object", ""), "Shape of object")
            or "others"
        )
        dimension = self.clean_dimension(entry.get("Dimension of object", ""))
        return {"shape": shape, "dimension": dimension}


class InstructionalFieldPostprocessor(BasePostprocessor):
    def run(self, val: str) -> dict:
        cleaned = self.clean_value(val)
        return {"instruction": "YES" if cleaned else "NO", "content": cleaned}

    def to_yes_no(self, val: str) -> str:
        cleaned = self.clean_value(val)
        return "NO" if not cleaned or cleaned.lower() == "no" else "YES"


class BasicFieldPostprocessor(BasePostprocessor):
    def run(self, entry: dict, field_name: str) -> str:
        return self.clean_value(entry.get(field_name, ""), field_name)


class MainPostprocessor:
    def __init__(self):
        self.product_code_processor = ProductCodePostprocessor()
        self.material_type_processor = MaterialTypePostprocessor()
        self.required_precision_processor = RequiredPrecisionPostprocessor()
        self.product_shape_processor = ProductShapePostprocessor()
        self.instructional_field_processor = InstructionalFieldPostprocessor()
        self.basic_processor = BasicFieldPostprocessor()

    def convert_to_output_format(self, entry: Dict) -> Dict:
        return {
            "ocr_product_code": self.product_code_processor.run(entry),
            "ocr_product_name": self.basic_processor.run(entry, "Product name"),
            "ocr_drawing_number": self.basic_processor.run(entry, "Product code"),
            "ocr_drawing_issuer": self.basic_processor.run(entry, "Customer"),
            "material_type": self.material_type_processor.run(entry),
            "required_precision": self.required_precision_processor.run(entry),
            "product_shape": self.product_shape_processor.run(entry),
            "processing_content": {
                "processing_surface": 0,
                "processing_locations": 0,
                "number_of_special_processing_locations": 0,
            },
            "lathe_processing_content": {
                "processing_surface": 0,
                "processing_locations": 0,
                "number_of_special_processing_locations": 0,
            },
            "surface_roughness": self.basic_processor.run(entry, "Surface roughness"),
            "polishing": self.instructional_field_processor.to_yes_no(
                entry.get("Polishing", "")
            ),
            "surface_treatment": self.instructional_field_processor.run(
                entry.get("Surface treatment", "")
            ),
            "heat_treatment": self.instructional_field_processor.run(
                entry.get("Heat treatment", "")
            ),
            "painting": self.instructional_field_processor.to_yes_no(
                entry.get("Painting", "")
            ),
        }

    def parse_model_output(self, text: str) -> List[Dict]:
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
        "Material type": "kkkk",
        "Customer": "TOYOTA BOSHOKU CORPORATION",
        "Heat treatment": "MTB",
        "Surface treatment": "GC",
        "Shape of object": "round",
        "Dimension of object": "",
        "Tolerance grade": "coarse grade",
        "Dimensional tolerance": "±0.09",
        "Polishing": "Yes",
        "Painting": "Yes",
        "Surface roughness": "Ra0.8"
        }
        ```
    """
    processor = MainPostprocessor()
    parsed_output = processor.parse_model_output(raw_output)
    print(json.dumps(parsed_output[0], indent=2, ensure_ascii=False))
