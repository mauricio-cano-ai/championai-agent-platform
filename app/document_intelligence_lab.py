from __future__ import annotations

import base64
import io
import os

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw
from pydantic import BaseModel


class ManufacturingDocument(BaseModel):
    document_type: str
    supplier: str
    lot_number: str
    material: str
    quantity: int
    unit: str
    inspection_status: str


def _make_document() -> str:
    image = Image.new("RGB", (1200, 700), "white")
    draw = ImageDraw.Draw(image)

    lines = [
        "CERTIFICATE OF ANALYSIS",
        "",
        "Supplier: Acme Industrial Materials",
        "Lot Number: LOT-84721",
        "Material: Food Grade Resin R90",
        "Quantity: 1250 KG",
        "Inspection Status: ACCEPTED",
    ]

    y = 80
    for line in lines:
        draw.text((90, y), line, fill="black")
        y += 70

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _parsed(response) -> ManufacturingDocument:
    for output in response.output:
        if output.type != "message":
            continue
        for item in output.content:
            if item.type == "output_text" and item.parsed is not None:
                return item.parsed
    raise RuntimeError("No structured document extraction returned.")


def main() -> None:
    load_dotenv()

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    response = client.responses.parse(
        model=model,
        instructions=(
            "Extract the manufacturing document into the requested "
            "schema. Preserve printed values; do not invent fields."
        ),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Extract this certificate into structured data."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": _make_document(),
                        "detail": "high",
                    },
                ],
            }
        ],
        text_format=ManufacturingDocument,
    )

    document = _parsed(response)

    print(document.model_dump_json(indent=2))

    assert document.supplier == "Acme Industrial Materials"
    assert document.lot_number == "LOT-84721"
    assert document.material == "Food Grade Resin R90"
    assert document.quantity == 1250
    assert document.unit.upper() == "KG"
    assert document.inspection_status.upper() == "ACCEPTED"

    print("DOCUMENT_INTELLIGENCE=PASS")


if __name__ == "__main__":
    main()
