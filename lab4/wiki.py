from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import wikipedia 

wikipedia.set_lang("ru")

app = FastAPI()

class SummaryResponse(BaseModel):
    title: str
    summary: str

class ArticleRequest(BaseModel):
    title: str = Field(min_length=1)

@app.get("/wiki/path/{title}")
def search_path(title: str):
    try:
        summary = wikipedia.summary(title)
        page = wikipedia.page(title)
        return SummaryResponse(title=page.title, summary=summary)
    except wikipedia.DisambiguationError as e:
        raise HTTPException(status_code=300, detail=f"Неоднозначный запрос. Уточните: {e.options[:5]}")
    except wikipedia.PageError:
        raise HTTPException(status_code=404, detail=f"Статья '{title}' не найдена")

@app.get("/wiki/query")
def search_query(title: str):
    try:
        summary = wikipedia.summary(title)
        page = wikipedia.page(title)
        return SummaryResponse(title=page.title, summary=summary)
    except wikipedia.DisambiguationError as e:
        raise HTTPException(status_code=300, detail=f"Неоднозначный запрос. Уточните: {e.options[:5]}")
    except wikipedia.PageError:
        raise HTTPException(status_code=404, detail=f"Статья '{title}' не найдена")

@app.post("/wiki/body")
def search_body(body: ArticleRequest):
    try:
        summary = wikipedia.summary(body.title)
        page = wikipedia.page(body.title)
        return SummaryResponse(title=page.title, summary=summary)
    except wikipedia.DisambiguationError as e:
        raise HTTPException(status_code=300, detail=f"Неоднозначный запрос. Уточните: {e.options[:5]}")
    except wikipedia.PageError:
        raise HTTPException(status_code=404, detail=f"Статья '{body.title}' не найдена")
    
if __name__ == "__main__":
    uvicorn.run("wiki:app", reload=True)
