import os
from google import genai
from google.genai import types

key = os.environ["VERTEX_AI_KEY"]
models = [
    "gemini-2.5-flash-image",
    "gemini-2.5-flash-image-preview",
    "gemini-3.1-flash-image",
    "gemini-2.0-flash-preview-image-generation",
]
for vertex in (False, True):
    print("MODE", "vertex" if vertex else "studio")
    client = genai.Client(vertexai=vertex, api_key=key)
    for model in models:
        try:
            r = client.models.generate_content(
                model=model,
                contents="A simple cream studio background, no people, square photo.",
                config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
            )
            has = False
            if r.candidates:
                for p in r.candidates[0].content.parts or []:
                    if getattr(p, "inline_data", None) and p.inline_data.data:
                        has = True
            print(" OK", model, "image" if has else "no-image", (r.text or "")[:80])
            if has:
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception as e:
            print(" FAIL", model, type(e).__name__, str(e)[:180])
print("NONE")
