from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
import uvicorn
import pyjokes

app = FastAPI()

class Joke(BaseModel):
    friend: str
    joke: str

class JokeInput(BaseModel):
    friend: str = Field(min_length=2)

@app.post("/", status_code=201)
def create_joke(joke_input: JokeInput):
    return Joke(friend=joke_input.friend, joke=pyjokes.get_joke())

@app.get("/", status_code=200)
def joke():
    return pyjokes.get_joke()

@app.get("/joke/{friend}", status_code=200)
def joke_by_path(friend: str):
    return Joke(friend=friend, joke=pyjokes.get_joke())

@app.get("/joke", status_code=200)
def joke_by_query(friend: str):
    return Joke(friend=friend, joke=pyjokes.get_joke())

@app.get("/{friend}", status_code=200)
def friends_joke(friend: str, jokes_number: int):
    if not (1 <= jokes_number <= 10):
        raise HTTPException(
            status_code=400,
            detail="jokes_number must be between 1 and 10"
        )
    result = ""
    for i in range(jokes_number):
        result += f"{friend} tells his joke #{i + 1}: {pyjokes.get_joke()}\n\n"
    return PlainTextResponse(result)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


