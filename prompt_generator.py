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
                            """
                                    Analyze the provided technical drawing, which may contain text in English and Japanese.

                                    Your task is to accurately extract the following information from the image.
                                    For each field, provide the extracted value exactly as written in the image, without making assumptions. If the field is not present or unclear, leave it blank.

                                    Return your output in the following key-value format, using one line per field:                                    

                                    Product name: [value]
                                    Product code: [value]
                                    Material code: [value]
                                    Material type: [value]  # Choose from: stainless steel, iron, aluminum, casting, brass, copper
                                    Customer: [value]
                                    Heat treatment: [value]  # Choose from: quenching, high-frequency quenching, tempering, normalizing, carburizing, vacuum heat treatment, or 'None of the above'
                                    Surface treatment: [value]  # Choose from: anodizing, non-electrolytic plating, black dyeing or blackening, phosphate manganese coating, trivalent chromate (ZMC3), hard chrome plating, or 'None of the above'
                                    Shape of object: [value]  # Choose from: round, angle, plate, or others
                                    Dimension of object: [value]  # Format like: 100x50x25 or ⌀30x150
                                    Tolerance grade: [value]  # Choose from: Fine grade, Medium grade, Coarse grade, Very coarse grade, or Not selected
                                    Dimensional tolerance: [value]  # e.g., ±0.1, ±0.01, general tolerance
                                    Polishing: [Yes/No]
                                    Painting: [Yes/No]
                                    Surface roughness: [value]  # Choose from: G, 0.8, 1.6, 3.2
                                 """
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
