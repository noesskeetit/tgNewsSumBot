from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import uvicorn

app = FastAPI()

# Инициализация Summarizer
# summarizer = pipeline('summarization', model='facebook/bart-large-cnn')
summarizer = pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')

class TextInput(BaseModel):
    text: str

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/summarize")
async def summarize_text(input_data: TextInput):
    try:
        # Если текста мало, возвращаем как есть
        if not input_data.text or len(input_data.text.split()) < 10:
            return {"summary": input_data.text}

        result = summarizer(input_data.text, max_length=150, min_length=30)
        return {"summary": result[0]['summary_text']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
