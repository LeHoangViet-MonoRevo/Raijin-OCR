import re


def parse_model_output(model_output: str):
    entries = []
    blocks = model_output.split(
        "================================================================================"
    )

    for block in blocks:
        data = {}
        lines = block.strip().splitlines()
        for line in lines:
            match = re.match(r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                data[key] = value

        if data:
            output = {
                "ocr_product_code": data.get("Product code", ""),
                "ocr_product_name": data.get("Product name", ""),
                "ocr_drawing_number": data.get(
                    "Product code", ""
                ),  # Duplicate of product code
                "ocr_drawing_issuer": data.get("Customer", ""),
                "material_type": {
                    "material_code": data.get("Material code", ""),
                    "material_type": data.get("Material type", ""),
                },
                "required_precision": {
                    "tolerance_grade": data.get("Tolerance grade", ""),
                    "dimensional_tolerance": data.get("Dimensional tolerance", ""),
                },
                "product_shape": {
                    "shape": data.get("Shape of object", "OTHERS"),
                    "dimension": data.get("Dimension of object", "0x0x0")
                    .replace("×", "x")
                    .replace(" ", ""),
                },
                "surface_roughness": data.get("Surface roughness", ""),
                "polishing": data.get("Polishing", ""),
                "surface_treatment": {
                    "instruction": (
                        "NO"
                        if data.get("Surface treatment", "").lower()
                        in ["", "none of the above"]
                        else "YES"
                    ),
                    "content": (
                        ""
                        if data.get("Surface treatment", "").lower()
                        in ["", "none of the above"]
                        else data.get("Surface treatment", "")
                    ),
                },
                "heat_treatment": {
                    "instruction": (
                        "NO"
                        if data.get("Heat treatment", "").lower()
                        in ["", "none of the above"]
                        else "YES"
                    ),
                    "content": (
                        ""
                        if data.get("Heat treatment", "").lower()
                        in ["", "none of the above"]
                        else data.get("Heat treatment", "")
                    ),
                },
                "painting": (
                    "NO"
                    if data.get("Painting", "").lower()
                    in ["", "no", "none of the above"]
                    else "YES"
                ),
            }
            entries.append(output)

    return entries


if __name__ == "__main__":
    output = """| Field                | Extracted Value                      |
|----------------------|--------------------------------------|
| Product name         | Hinge, RR Seat Back, CTR           |
| Product code         | 71343-X1UP0                       |
| Material code        | 02X(F)                          |
| Material type        | None of the above                 |
| Customer             | MTEC                           |
| Heat treatment       | None of the above               |
| Surface treatment    | None of the above              |
| Shape of object      | Angle                         |
| Dimension of object  | Diameter × Length              |
| Tolerance grade      | Not selected                   |
| Dimensional tolerance| Not selected                   |
| Polishing            | Yes                            |
| Painting             | Yes                            |
| Surface roughness    | None of the above              |"""
parsed_output = parse_model_output(output)
print(f"parsed_output: {parsed_output}")
