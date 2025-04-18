import json
import re
from typing import Dict, List, Union


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

    def clean_value(
        self, val: str, allowed_values: Union[List[str], None] = None
    ) -> str:
        try:
            if not val:
                return ""

            val_cleaned = self.strip_wrappers(val).strip()
            val_lower = val_cleaned.lower()

            # Discard if it's in the disallowed junk list
            if val_lower in self.DISALLOWED_VALUES:
                return ""

            # If allowed values are defined, check against them (case-insensitive)
            if allowed_values:
                allowed_set = {a.lower() for a in allowed_values}
                if val_lower not in allowed_set:
                    return ""

            return val_cleaned
        except Exception:
            return ""


class ProductCodePostprocessor(BasePostprocessor):
    PRODUCT_CODE_FIELD_KEY = "Product code"

    def run(self, entry: Dict) -> str:
        return self.clean_value(
            val=entry.get(self.PRODUCT_CODE_FIELD_KEY), allowed_values=None
        )


class MaterialTypePostprocessor(BasePostprocessor):
    ALLOWED_MATERIAL_TYPES = [
        "stainless steel",
        "iron",
        "aluminum",
        "cast metal",
        "brass",
        "copper",
    ]

    MATERIAL_CODE_FIELD_KEY = "Material code"
    MATERIAL_TYPE_FIELD_KEY = "Material type"

    def run(self, entry: Dict) -> Dict:
        code = self.clean_value(
            val=entry.get(self.MATERIAL_CODE_FIELD_KEY), allowed_values=None
        )
        material = self.clean_value(
            val=entry.get(self.MATERIAL_TYPE_FIELD_KEY),
            allowed_values=self.ALLOWED_MATERIAL_TYPES,
        )

        return {"material_code": code, "material_type": material}


class RequiredPrecisionPostprocessor(BasePostprocessor):
    ALLOWED_TOLERANCES = ["±0.001", "±0.01", "±0.1"]
    TOLERANCE_GRADE_FIELD_NAME = "Tolerance grade"
    DIMENSIONAL_TOLERANCE_FIELD_NAME = "Dimensional tolerance"

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

    def run(self, entry: Dict) -> Dict:
        grade = self.clean_value(
            val=entry.get(self.TOLERANCE_GRADE_FIELD_NAME), allowed_values=None
        )
        raw_tol = entry.get(self.DIMENSIONAL_TOLERANCE_FIELD_NAME)
        most_precise = self.get_most_precise_dimensional_tolerance(raw_tol)
        category = self.classify_tolerance(most_precise)
        return {
            "tolerance_grade": grade,
            "dimensional_tolerance": category,
        }


class ProductShapePostprocessor(BasePostprocessor):
    ALLOWED_SHAPES = ["round", "angle", "plate", "others"]
    OBJECT_SHAPE_FIELD_NAME = "Shape of object"
    OBJECT_DIMENSION_FIELD_NAME = "Dimension of object"

    def convert_phi_to_box(self, value: str, default_value: str = "0x0x0") -> str:
        try:
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

            return default_value
        except Exception:
            return default_value

    def clean_dimension(self, value: str, default_value: str = "0x0x0") -> str:
        try:
            if not value:
                return default_value
            value = self.strip_wrappers(value)
            value = value.replace("×", "x").replace(" ", "").strip()

            # Attempt phi-style interpretation
            phi_box = self.convert_phi_to_box(value)
            if phi_box != default_value:
                return phi_box

            # Standard 3-component format
            parts = value.split("x")
            if len(parts) == 3 and all("⌀" not in p for p in parts):
                float(parts[0])
                float(parts[1])
                float(parts[2])
                return "x".join(parts)

            return default_value
        except Exception:
            return default_value

    def run(self, entry: Dict) -> Dict:
        shape = (
            self.clean_value(
                val=entry.get(self.OBJECT_SHAPE_FIELD_NAME),
                allowed_values=self.ALLOWED_SHAPES,
            )
            or "others"
        )
        dimension = self.clean_dimension(entry.get(self.OBJECT_DIMENSION_FIELD_NAME))
        return {"shape": shape, "dimension": dimension}


class InstructionalFieldPostprocessor(BasePostprocessor):
    def run(self, val: str) -> Dict:
        cleaned = self.clean_value(val)
        return {"instruction": "YES" if cleaned else "NO", "content": cleaned}

    def to_yes_no(self, val: str) -> str:
        cleaned = self.clean_value(val)
        return "YES" if cleaned.lower() == "yes" else "NO"


class BasicFieldPostprocessor(BasePostprocessor):
    def run(self, entry: Dict, field_name: str) -> str:
        return self.clean_value(val=entry.get(field_name, ""), allowed_values=None)


class SurfaceRoughnessFieldPostprocessor(BasePostprocessor):
    ALLOWED_SURFACE_ROUGHNESS = [
        "Ra0.4",
        "Ra0.8",
        "Ra1.6",
        "Ra3.2",
        "Ra6.3",
        "Ra12.5",
        "Ra25~",
    ]
    SR_FIELD_NAME = "Surface roughness"

    def run(self, entry: Dict):
        return self.clean_value(
            val=entry.get(self.SR_FIELD_NAME),
            allowed_values=self.ALLOWED_SURFACE_ROUGHNESS,
        )


class MainPostprocessor:
    def __init__(self):
        self.product_code_processor = ProductCodePostprocessor()
        self.material_type_processor = MaterialTypePostprocessor()
        self.required_precision_processor = RequiredPrecisionPostprocessor()
        self.product_shape_processor = ProductShapePostprocessor()
        self.instructional_field_processor = InstructionalFieldPostprocessor()
        self.surface_roughness_field_processor = SurfaceRoughnessFieldPostprocessor()
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
            "surface_roughness": self.surface_roughness_field_processor.run(entry),
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

    def parse_model_output(self, text: str) -> Dict:
        try:
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_match:
                entry = json.loads(json_match.group(1))
            else:
                entry = {}
                for line in text.strip().splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        entry[key.strip()] = value.strip()

            return self.convert_to_output_format(entry)
        except Exception:
            return self.convert_to_output_format({})


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
        "Dimension of object": "6.96x1.34x1.234",
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
    print(json.dumps(parsed_output, indent=2, ensure_ascii=False))
