# PPL Compiler

A compiler for the PPL (Programming Practice Language) that lexes, parses, performs semantic analysis, and generates C code.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Lexer only
```bash
python3 lexer/lexer.py example
```

### Full Compilation
```bash
python -m compiler.compiler <source_file> [--run]
```

Example:
```bash
python -m compiler.compiler tests/hello.ppl --run
```

## Components

- **lexer/**: Tokenizes PPL source code
- **parser/**: Parses tokens into an Abstract Syntax Tree (AST)
- **semantic/**: Performs type checking and name resolution
- **codegen/**: Generates C code from the AST and compiles with GCC
- **tests/**: Test cases for the compiler

## Language Features

- Classes with inheritance and polymorphism
- Functions with type annotations
- Variable declarations with optional type inference
- Control flow: if/else, while, for loops
- Arithmetic and logical expressions
- Built-in `print` and `read` functions

## Example

```ppl
fn main(): int {
    print("Hello, World!");
    return 0;
}
```