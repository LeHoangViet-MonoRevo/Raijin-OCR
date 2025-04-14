class Prompt(object):
    @staticmethod
    def technical_drawing_extraction_prompt(
        image_path: str, resized_width: int = 3840, resized_height: int = 2160
    ):

        prompt = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image_path,
                        "resized_height": resized_height,
                        "resized_width": resized_width,
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analyze the provided technical drawing, which may contain text in English and Japanese.\n\n"
                            "Your task is to accurately extract the following information from the image:\n"
                            "1. Product name\n"
                            "2. Product code\n"
                            "3. Material code\n"
                            "4. Material type (if identifiable, classify as: stainless steel, iron, aluminum, casting, brass, copper)\n"
                            "5. Customer\n"
                            "6. Heat treatment (classify if present into: quenching, high-frequency quenching, tempering, normalizing, carburizing, vacuum heat treatment, or 'None of the above')\n"
                            "7. Surface treatment (classify if present into: anodizing, non-electrolytic plating, black dyeing or blackening, phosphate manganese coating, trivalent chromate (ZMC3), hard chrome plating, or 'None of the above')\n"
                            "8. Shape of object (classify as: round, angle, plate, or others based on the drawing\n"
                            "9. Dimension of object (e.g., width × length × height or diameter × length)\n"
                            "10. Tolerance grade (公差等级) — classify into: Fine grade, Medium grade, Coarse grade, Very coarse grade, or Not selected\n"
                            "11. Dimensional tolerance (尺寸公差) — numerical format like general tolerance, ±0.1, ±0.01, ±0.001\n"
                            "12. Polishing (Yes or No)\n"
                            "13. Painting (Yes or No)\n"
                            "14. Surface roughness (classify if available: G, 0.8, 1.6, 3.2)\n\n"
                            "If any of these fields are missing in the image, leave the corresponding entry blank. "
                            "Do not make assumptions or generate content that is not explicitly visible in the image.\n\n"
                            "Please return the extracted information in the following table format:\n\n"
                            "| Field                | Extracted Value                      |\n"
                            "|----------------------|--------------------------------------|\n"
                            "| Product name         |                                      |\n"
                            "| Product code         |                                      |\n"
                            "| Material code        |                                      |\n"
                            "| Material type        |                                      |\n"
                            "| Customer             |                                      |\n"
                            "| Heat treatment       |                                      |\n"
                            "| Surface treatment    |                                      |\n"
                            "| Shape of object      |                                      |\n"
                            "| Dimension of object  |                                      |\n"
                            "| Tolerance grade      |                                      |\n"
                            "| Dimensional tolerance|                                      |\n"
                            "| Polishing            |                                      |\n"
                            "| Painting             |                                      |\n"
                            "| Surface roughness    |                                      |"
                        ),
                    },
                ],
            }
        ]

        return prompt


class OutputFormat(object):
    data = {
        "ocr_product_code": "",
        "ocr_product_name": "",
        "ocr_drawing_number": "",
        "ocr_drawing_issuer": "",
        "material_type": {"material_code": "", "material_type": ""},
        "required_precision": {
            "tolerance_grade": "PRECISION_GRADE",
            "dimensional_tolerance": "GENERAL_TOLERANCE",
        },
        "product_shape": {"shape": "OTHERS", "dimension": "0x0x0"},
        "surface_roughness": "",
        "polishing": "",
        "surface_treatment": {"instruction": "NO", "content": ""},
        "heat_treatment": {"instruction": "NO", "content": ""},
        "painting": "NO",
    }


if __name__ == "__main__":
    output = OutputFormat.data
    print(f"Output: {output}")
