"""Test cases for the PPL compiler."""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from compiler.compiler import compile_source


def test_hello_world():
    """Test simple hello world program."""
    code = '''
fn main(): int {
    print("Hello, World!");
    return 0;
}
'''
    result = compile_source(code, run=True)
    assert result.success, f"Compilation failed: {result.errors}"
    assert "Hello, World!" in result.output


def test_arithmetic():
    """Test arithmetic operations."""
    code = '''
fn main(): int {
    let x: int = 5;
    let y: int = 10;
    let sum: int = x + y;
    return 0;
}
'''
    result = compile_source(code, run=True)
    assert result.success, f"Compilation failed: {result.errors}"


def test_type_inference():
    """Test type inference."""
    code = '''
fn main(): int {
    let x = 42;
    let y = 3.14;
    let s = "hello";
    return 0;
}
'''
    result = compile_source(code, run=True)
    assert result.success, f"Compilation failed: {result.errors}"


def test_if_statement():
    """Test if statement."""
    code = '''
fn main(): int {
    let x: int = 5;
    if x > 0 {
        print("positive");
    } else {
        print("non-positive");
    }
    return 0;
}
'''
    result = compile_source(code, run=True)
    assert result.success, f"Compilation failed: {result.errors}"
    assert "positive" in result.output


def test_while_loop():
    """Test while loop."""
    code = '''
fn main(): int {
    let i: int = 0;
    while i < 3 {
        print("loop");
        i = i + 1;
    }
    return 0;
}
'''
    result = compile_source(code, run=True)
    assert result.success, f"Compilation failed: {result.errors}"


def test_class_definition():
    """Test class definition."""
    code = '''
class Point {
    x: int
    y: int
    
    fn Point() {
    }
    
    fn getX(): int {
        return 1;
    }
}

fn main(): int {
    return 0;
}
'''
    result = compile_source(code, run=True)
    assert result.success, f"Compilation failed: {result.errors}"


def test_semantic_error_type_mismatch():
    """Test type mismatch detection."""
    code = '''
fn main(): int {
    let x: int = "hello";
    return 0;
}
'''
    result = compile_source(code, run=False)
    assert not result.success
    assert any("Type mismatch" in e.message for e in result.errors)


def test_semantic_error_undefined_variable():
    """Test undefined variable detection."""
    code = '''
fn main(): int {
    let x: int = undefinedVar;
    return 0;
}
'''
    result = compile_source(code, run=False)
    assert not result.success
    assert any("Undefined variable" in e.message for e in result.errors)


def test_semantic_error_no_main():
    """Test missing main function detection."""
    code = '''
fn foo(): int {
    return 0;
}
'''
    result = compile_source(code, run=False)
    assert not result.success
    assert any("main" in e.message.lower() for e in result.errors)


if __name__ == "__main__":
    tests = [
        test_hello_world,
        test_arithmetic,
        test_type_inference,
        test_if_statement,
        test_while_loop,
        test_class_definition,
        test_semantic_error_type_mismatch,
        test_semantic_error_undefined_variable,
        test_semantic_error_no_main,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
