from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from compiler.lexer.lexer import Lexer, TokenKind
from tabulate import tabulate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class RunRequest(BaseModel):
    code: str


@app.get("/")
def check():
    return {"status": "ok"}


@app.post("/run")
def run_code(req: RunRequest):
    lexer = Lexer(req.code)
    tokens = []

    while True:
        tok = lexer.lex()
        if tok.kind == TokenKind.EOF:
            break

        tokens.append({
            "kind": tok.kind.name,
            "value": tok.value,
            "line": tok.linenum,
            "column": tok.column,
            "diagnostic": tok.diagnostic
        })

    return {"tokens": tokens}


@app.post("/download")
def download(req: RunRequest):
    items = [["Token Kind", "Token Value"]]
    l = Lexer(req.code)

    while not (tok := l.lex()).eof():
        items.append([tok.kind.name, tok.value])

    table = tabulate(items, headers="firstrow")

    return PlainTextResponse(
        table,
        headers={
            "Content-Disposition": "attachment; filename=lexical_table.txt"
        }
    )
