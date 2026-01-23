"""Main compiler module that integrates lexer, parser, semantic analyzer, and code generator."""
from dataclasses import dataclass
from typing import Optional
from compiler.lexer.lexer import Lexer
from compiler.parser.parser import Parser, ParseError
from compiler.semantic.analyzer import SemanticAnalyzer, SemanticError
from compiler.codegen.generator import CodeGenerator, compile_and_run


@dataclass
class CompilationError:
    """Represents a compilation error."""
    stage: str  # "lexer", "parser", "semantic", "codegen"
    message: str
    line: int
    column: int


@dataclass  
class CompilationResult:
    """Result of compilation."""
    success: bool
    errors: list[CompilationError]
    c_code: Optional[str] = None
    output: Optional[str] = None
    tokens: list = None
    ast: any = None


class Compiler:
    """Main compiler class that orchestrates the compilation pipeline."""
    
    def __init__(self, source: str):
        self.source = source
        self.errors: list[CompilationError] = []
    
    def compile(self, run: bool = False) -> CompilationResult:
        """
        Compile the source code through all stages.
        
        Args:
            run: If True, also compile the generated C code and run it.
        
        Returns:
            CompilationResult with success status and any errors/output.
        """
        # Stage 1: Lexing
        lexer = Lexer(self.source)
        tokens = []
        while True:
            tok = lexer.lex()
            tokens.append(tok)
            if tok.eof():
                break
            if tok.diagnostic:
                self.errors.append(CompilationError(
                    stage="lexer",
                    message=tok.diagnostic,
                    line=tok.linenum,
                    column=tok.column
                ))
        
        if self.errors:
            return CompilationResult(
                success=False,
                errors=self.errors,
                tokens=tokens
            )
        
        # Stage 2: Parsing
        lexer = Lexer(self.source)  # Reset lexer
        parser = Parser(lexer)
        
        try:
            ast = parser.parse()
        except ParseError as e:
            self.errors.append(CompilationError(
                stage="parser",
                message=e.message,
                line=e.token.linenum,
                column=e.token.column
            ))
            return CompilationResult(
                success=False,
                errors=self.errors,
                tokens=tokens
            )
        
        # Add any non-fatal parse errors
        for error in parser.errors:
            self.errors.append(CompilationError(
                stage="parser",
                message=error.message,
                line=error.token.linenum,
                column=error.token.column
            ))
        
        if self.errors:
            return CompilationResult(
                success=False,
                errors=self.errors,
                tokens=tokens,
                ast=ast
            )
        
        # Stage 3: Semantic Analysis
        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast)
        
        for error in semantic_errors:
            self.errors.append(CompilationError(
                stage="semantic",
                message=error.message,
                line=error.line,
                column=error.column
            ))
        
        if self.errors:
            return CompilationResult(
                success=False,
                errors=self.errors,
                tokens=tokens,
                ast=ast
            )
        
        # Stage 4: Code Generation
        generator = CodeGenerator()
        c_code = generator.generate(ast)
        
        output = None
        if run:
            success, output = compile_and_run(c_code)
            if not success:
                self.errors.append(CompilationError(
                    stage="codegen",
                    message=output,
                    line=0,
                    column=0
                ))
                return CompilationResult(
                    success=False,
                    errors=self.errors,
                    tokens=tokens,
                    ast=ast,
                    c_code=c_code
                )
        
        return CompilationResult(
            success=True,
            errors=[],
            tokens=tokens,
            ast=ast,
            c_code=c_code,
            output=output
        )


def compile_source(source: str, run: bool = False) -> CompilationResult:
    """Convenience function to compile source code."""
    compiler = Compiler(source)
    return compiler.compile(run=run)


def compile_file(filename: str, run: bool = False) -> CompilationResult:
    """Compile source code from a file."""
    with open(filename, 'r') as f:
        source = f.read()
    return compile_source(source, run=run)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print(f"Usage: python -m compiler.compiler <source_file> [--run]")
        sys.exit(1)
    
    filename = sys.argv[1]
    run = "--run" in sys.argv
    
    result = compile_file(filename, run=run)
    
    if result.success:
        print("Compilation successful!")
        if result.c_code:
            print("\n--- Generated C Code ---")
            print(result.c_code)
        if result.output:
            print("\n--- Program Output ---")
            print(result.output)
    else:
        print("Compilation failed:")
        for error in result.errors:
            print(f"  [{error.stage}] Line {error.line}, Column {error.column}: {error.message}")
        sys.exit(1)
