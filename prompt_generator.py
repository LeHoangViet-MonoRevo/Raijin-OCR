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
                            "1. Name of this product\n"
                            "2. Product Code\n"
                            "3. Material\n"
                            "4. Customer\n"
                            "5. Heat treatment\n"
                            "6. Surface treatment\n"
                            "7. Shape of object (angle, round, plate or other)\n"
                            "8. Dimension of object\n"
                            "9. Tolerance (classify into: Fine grade, Medium grade, Coarse grade, Very coarse grade, or Not selected)\n"
                            "10. Polishing (Yes or No)\n"
                            "11. Painting content\n\n"
                            "If any of these fields are missing in the image, leave the corresponding entry blank. "
                            "Do not make assumptions or generate content that is not explicitly visible in the image.\n\n"
                            "Please return the extracted information in the following table format:\n\n"
                            "| Field                | Extracted Value                      |\n"
                            "|----------------------|--------------------------------------|\n"
                            "| Product name         |                                      |\n"
                            "| Product Code         |                                      |\n"
                            "| Material             |                                      |\n"
                            "| Customer             |                                      |\n"
                            "| Heat treatment       |                                      |\n"
                            "| Surface treatment    |                                      |\n"
                            "| Shape of object      |                                      |\n"
                            "| Dimension of object  |                                      |\n"
                            "| Tolerance            |                                      |\n"
                            "| Polishing            |                                      |\n"
                            "| Painting content     |                                      |"
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
        "surface_roughness": "",
        "polishing": "",
        "surface_treatment": {"instruction": "NO", "content": ""},
        "heat_treatment": {"instruction": "NO", "content": ""},
        "painting": "NO",
    }

if __name__ == "__main__":
    output = OutputFormat.data
    print(f"Output: {output}")