import os

import openai
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

open_api_key = os.getenv("OPENAI_API_KEY")


# Function to convert Figma JSON to HTML using OpenAI
def convert_figma_to_html(figma_json: Dict) -> str:
    openai.api_key = open_api_key
    prompt = f"Convert the following Figma JSON to HTML and CSS:\n{json.dumps(figma_json)}"
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=3000,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text


@app.post("/convert/")
async def convert(figma_file: UploadFile = File(...)):
    openai.api_key = open_api_key
    if not open_api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key is required")

    figma_json = json.loads(await figma_file.read())
    try:
        html_output = convert_figma_to_html(figma_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"html_output": html_output}
