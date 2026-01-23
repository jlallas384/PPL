from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from compiler.lexer.lexer import Lexer, TokenKind
from compiler.compiler import compile_source
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


class CompileRequest(BaseModel):
    code: str
    run: bool = False


@app.post("/compile")
def compile_code(req: CompileRequest):
    """Compile the source code through all stages."""
    result = compile_source(req.code, run=req.run)
    
    errors = []
    for error in result.errors:
        errors.append({
            "stage": error.stage,
            "message": error.message,
            "line": error.line,
            "column": error.column
        })
    
    return {
        "success": result.success,
        "errors": errors,
        "c_code": result.c_code,
        "output": result.output
    }


@app.post("/generate")
def generate_code(req: RunRequest):
    """Generate C code from source (no execution)."""
    result = compile_source(req.code, run=False)
    
    errors = []
    for error in result.errors:
        errors.append({
            "stage": error.stage,
            "message": error.message,
            "line": error.line,
            "column": error.column
        })
    
    return {
        "success": result.success,
        "errors": errors,
        "c_code": result.c_code
    }
