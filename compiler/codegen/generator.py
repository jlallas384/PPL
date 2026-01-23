"""Code generator for the PPL language - transpiles to C and compiles with GCC."""
import subprocess
import tempfile
import os
from typing import Optional
from compiler.parser.ast import (
    Program, ClassDecl, FunctionDecl, FieldDecl, Parameter, TypeNode,
    Stmt, VarDecl, Assignment, IfStmt, WhileStmt, ForStmt, ReturnStmt,
    BreakStmt, ContinueStmt, Block, ExprStmt, Expr, IntLiteral, FloatLiteral,
    StringLiteral, CharLiteral, BoolLiteral, Identifier, BinaryExpr,
    UnaryExpr, CallExpr, MemberExpr, NewExpr, IndexExpr, BinaryOp, UnaryOp, AssignOp
)


class CodeGenerator:
    """Generates C code from the PPL AST."""
    
    def __init__(self):
        self.output = []
        self.indent_level = 0
        self.class_info: dict[str, ClassDecl] = {}
    
    def emit(self, line: str = ""):
        """Emit a line of code with proper indentation."""
        if line:
            self.output.append("    " * self.indent_level + line)
        else:
            self.output.append("")
    
    def generate(self, program: Program) -> str:
        """Generate C code from the program AST."""
        # Build class info
        for cls in program.classes:
            self.class_info[cls.name] = cls
        
        # Header
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("#include <string.h>")
        self.emit("#include <stdbool.h>")
        self.emit()
        
        # Forward declarations
        for cls in program.classes:
            self.emit(f"typedef struct {cls.name} {cls.name};")
        self.emit()
        
        # Generate class structures and vtables
        for cls in program.classes:
            self._generate_class_struct(cls)
        
        # Generate vtable types and instances
        for cls in program.classes:
            self._generate_vtable(cls)
        
        # Generate function prototypes
        for func in program.functions:
            self._generate_function_prototype(func)
        self.emit()
        
        # Generate class method implementations
        for cls in program.classes:
            self._generate_class_methods(cls)
        
        # Generate function implementations
        for func in program.functions:
            self._generate_function(func)
        
        return "\n".join(self.output)
    
    def _generate_class_struct(self, cls: ClassDecl):
        """Generate C struct for a class."""
        self.emit(f"// Class {cls.name}")
        self.emit(f"struct {cls.name} {{")
        self.indent_level += 1
        
        # Vtable pointer
        self.emit(f"struct {cls.name}_vtable* __vtable;")
        
        # Inherit base class fields
        if cls.base_class and cls.base_class in self.class_info:
            base = self.class_info[cls.base_class]
            for field in base.fields:
                c_type = self._type_to_c(field.type_annotation)
                self.emit(f"{c_type} {field.name};")
        
        # Own fields
        for field in cls.fields:
            c_type = self._type_to_c(field.type_annotation)
            self.emit(f"{c_type} {field.name};")
        
        self.indent_level -= 1
        self.emit("};")
        self.emit()
    
    def _generate_vtable(self, cls: ClassDecl):
        """Generate vtable structure and instance for polymorphism."""
        self.emit(f"// Vtable for {cls.name}")
        self.emit(f"struct {cls.name}_vtable {{")
        self.indent_level += 1
        
        # Collect all virtual methods
        methods = self._collect_virtual_methods(cls)
        for method_name, (return_type, params) in methods.items():
            param_str = self._params_to_c_with_self(cls.name, params)
            ret_type = self._type_to_c(return_type) if return_type else "void"
            self.emit(f"{ret_type} (*{method_name})({param_str});")
        
        self.indent_level -= 1
        self.emit("};")
        self.emit()
        
        # Generate vtable instance (will be filled in method section)
        self.emit(f"struct {cls.name}_vtable {cls.name}_vtable_instance;")
        self.emit()
    
    def _collect_virtual_methods(self, cls: ClassDecl) -> dict:
        """Collect all virtual methods including inherited ones."""
        methods = {}
        
        # Get base class methods first
        if cls.base_class and cls.base_class in self.class_info:
            base = self.class_info[cls.base_class]
            methods.update(self._collect_virtual_methods(base))
        
        # Add/override with own methods
        for method in cls.methods:
            if method.name != cls.name:  # Skip constructor
                methods[method.name] = (method.return_type, method.params)
        
        return methods
    
    def _generate_function_prototype(self, func: FunctionDecl):
        """Generate a C function prototype."""
        ret_type = self._type_to_c(func.return_type) if func.return_type else "void"
        params = self._params_to_c(func.params)
        self.emit(f"{ret_type} {func.name}({params});")
    
    def _generate_class_methods(self, cls: ClassDecl):
        """Generate method implementations for a class."""
        for method in cls.methods:
            if method.body:
                self._generate_method(cls, method)
        
        # Initialize vtable
        self._generate_vtable_init(cls)
    
    def _generate_method(self, cls: ClassDecl, method: FunctionDecl):
        """Generate a method implementation."""
        ret_type = self._type_to_c(method.return_type) if method.return_type else "void"
        params = self._params_to_c_with_self(cls.name, method.params)
        
        # Constructor
        if method.name == cls.name:
            self.emit(f"{cls.name}* {cls.name}_new({self._params_to_c(method.params)}) {{")
            self.indent_level += 1
            self.emit(f"{cls.name}* self = ({cls.name}*)malloc(sizeof({cls.name}));")
            self.emit(f"self->__vtable = &{cls.name}_vtable_instance;")
            
            for stmt in method.body:
                self._generate_stmt(stmt)
            
            self.emit("return self;")
            self.indent_level -= 1
            self.emit("}")
        else:
            self.emit(f"{ret_type} {cls.name}_{method.name}({params}) {{")
            self.indent_level += 1
            
            for stmt in method.body:
                self._generate_stmt(stmt)
            
            self.indent_level -= 1
            self.emit("}")
        
        self.emit()
    
    def _generate_vtable_init(self, cls: ClassDecl):
        """Generate vtable initialization."""
        self.emit(f"// Vtable initialization for {cls.name}")
        self.emit(f"void {cls.name}_vtable_init() {{")
        self.indent_level += 1
        
        methods = self._collect_virtual_methods(cls)
        for method_name in methods:
            # Check if this class implements the method
            impl_class = self._find_method_implementation(cls, method_name)
            if impl_class:
                self.emit(f"{cls.name}_vtable_instance.{method_name} = {impl_class}_{method_name};")
        
        self.indent_level -= 1
        self.emit("}")
        self.emit()
    
    def _find_method_implementation(self, cls: ClassDecl, method_name: str) -> Optional[str]:
        """Find which class implements a method."""
        for method in cls.methods:
            if method.name == method_name and method.body:
                return cls.name
        
        if cls.base_class and cls.base_class in self.class_info:
            return self._find_method_implementation(self.class_info[cls.base_class], method_name)
        
        return None
    
    def _generate_function(self, func: FunctionDecl):
        """Generate a function implementation."""
        if not func.body:
            return
        
        ret_type = self._type_to_c(func.return_type) if func.return_type else "void"
        params = self._params_to_c(func.params)
        
        self.emit(f"{ret_type} {func.name}({params}) {{")
        self.indent_level += 1
        
        for stmt in func.body:
            self._generate_stmt(stmt)
        
        self.indent_level -= 1
        self.emit("}")
        self.emit()
    
    def _generate_stmt(self, stmt: Stmt):
        """Generate C code for a statement."""
        if isinstance(stmt, VarDecl):
            self._generate_var_decl(stmt)
        elif isinstance(stmt, Assignment):
            self._generate_assignment(stmt)
        elif isinstance(stmt, IfStmt):
            self._generate_if_stmt(stmt)
        elif isinstance(stmt, WhileStmt):
            self._generate_while_stmt(stmt)
        elif isinstance(stmt, ForStmt):
            self._generate_for_stmt(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._generate_return_stmt(stmt)
        elif isinstance(stmt, BreakStmt):
            self.emit("break;")
        elif isinstance(stmt, ContinueStmt):
            self.emit("continue;")
        elif isinstance(stmt, Block):
            self.emit("{")
            self.indent_level += 1
            for s in stmt.statements:
                self._generate_stmt(s)
            self.indent_level -= 1
            self.emit("}")
        elif isinstance(stmt, ExprStmt):
            expr_code = self._generate_expr(stmt.expr)
            self.emit(f"{expr_code};")
    
    def _generate_var_decl(self, stmt: VarDecl):
        """Generate a variable declaration."""
        if stmt.type_annotation:
            c_type = self._type_to_c(stmt.type_annotation)
        else:
            # Type inference - need to infer from initializer
            c_type = self._infer_c_type(stmt.initializer)
        
        if stmt.initializer:
            init_code = self._generate_expr(stmt.initializer)
            self.emit(f"{c_type} {stmt.name} = {init_code};")
        else:
            self.emit(f"{c_type} {stmt.name};")
    
    def _generate_assignment(self, stmt: Assignment):
        """Generate an assignment statement."""
        target = self._generate_expr(stmt.target)
        value = self._generate_expr(stmt.value)
        
        op_map = {
            AssignOp.ASSIGN: "=",
            AssignOp.ADD_ASSIGN: "+=",
            AssignOp.SUB_ASSIGN: "-=",
            AssignOp.MUL_ASSIGN: "*=",
            AssignOp.DIV_ASSIGN: "/=",
            AssignOp.MOD_ASSIGN: "%="
        }
        
        op = op_map[stmt.op]
        self.emit(f"{target} {op} {value};")
    
    def _generate_if_stmt(self, stmt: IfStmt):
        """Generate an if statement."""
        cond = self._generate_expr(stmt.condition)
        self.emit(f"if ({cond}) {{")
        self.indent_level += 1
        
        for s in stmt.then_branch:
            self._generate_stmt(s)
        
        self.indent_level -= 1
        
        if stmt.else_branch:
            self.emit("} else {")
            self.indent_level += 1
            for s in stmt.else_branch:
                self._generate_stmt(s)
            self.indent_level -= 1
        
        self.emit("}")
    
    def _generate_while_stmt(self, stmt: WhileStmt):
        """Generate a while statement."""
        cond = self._generate_expr(stmt.condition)
        self.emit(f"while ({cond}) {{")
        self.indent_level += 1
        
        for s in stmt.body:
            self._generate_stmt(s)
        
        self.indent_level -= 1
        self.emit("}")
    
    def _generate_for_stmt(self, stmt: ForStmt):
        """Generate a for statement."""
        # For loops are tricky - emit as while loop
        self.emit("{")
        self.indent_level += 1
        
        if stmt.init:
            self._generate_stmt(stmt.init)
        
        cond = self._generate_expr(stmt.condition) if stmt.condition else "1"
        self.emit(f"while ({cond}) {{")
        self.indent_level += 1
        
        for s in stmt.body:
            self._generate_stmt(s)
        
        if stmt.update:
            self._generate_stmt(stmt.update)
        
        self.indent_level -= 1
        self.emit("}")
        
        self.indent_level -= 1
        self.emit("}")
    
    def _generate_return_stmt(self, stmt: ReturnStmt):
        """Generate a return statement."""
        if stmt.value:
            value = self._generate_expr(stmt.value)
            self.emit(f"return {value};")
        else:
            self.emit("return;")
    
    def _generate_expr(self, expr: Expr) -> str:
        """Generate C code for an expression."""
        if isinstance(expr, IntLiteral):
            return str(expr.value)
        elif isinstance(expr, FloatLiteral):
            return str(expr.value)
        elif isinstance(expr, StringLiteral):
            return expr.value  # Already has quotes
        elif isinstance(expr, CharLiteral):
            return expr.value  # Already has quotes
        elif isinstance(expr, BoolLiteral):
            return "true" if expr.value else "false"
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, BinaryExpr):
            return self._generate_binary_expr(expr)
        elif isinstance(expr, UnaryExpr):
            return self._generate_unary_expr(expr)
        elif isinstance(expr, CallExpr):
            return self._generate_call_expr(expr)
        elif isinstance(expr, MemberExpr):
            return self._generate_member_expr(expr)
        elif isinstance(expr, NewExpr):
            return self._generate_new_expr(expr)
        elif isinstance(expr, IndexExpr):
            return self._generate_index_expr(expr)
        
        return "/* unknown expr */"
    
    def _generate_binary_expr(self, expr: BinaryExpr) -> str:
        """Generate a binary expression."""
        left = self._generate_expr(expr.left)
        right = self._generate_expr(expr.right)
        
        op_map = {
            BinaryOp.ADD: "+",
            BinaryOp.SUB: "-",
            BinaryOp.MUL: "*",
            BinaryOp.DIV: "/",
            BinaryOp.MOD: "%",
            BinaryOp.EQ: "==",
            BinaryOp.NEQ: "!=",
            BinaryOp.LT: "<",
            BinaryOp.LEQ: "<=",
            BinaryOp.GT: ">",
            BinaryOp.GEQ: ">=",
            BinaryOp.AND: "&&",
            BinaryOp.OR: "||"
        }
        
        op = op_map.get(expr.op, "?")
        return f"({left} {op} {right})"
    
    def _generate_unary_expr(self, expr: UnaryExpr) -> str:
        """Generate a unary expression."""
        operand = self._generate_expr(expr.operand)
        
        if expr.op == UnaryOp.NEG:
            return f"(-{operand})"
        elif expr.op == UnaryOp.NOT:
            return f"(!{operand})"
        
        return operand
    
    def _generate_call_expr(self, expr: CallExpr) -> str:
        """Generate a function call expression."""
        args = ", ".join(self._generate_expr(arg) for arg in expr.arguments)
        
        if isinstance(expr.callee, Identifier):
            func_name = expr.callee.name
            # Handle built-in functions
            if func_name == "print":
                if expr.arguments:
                    arg = expr.arguments[0]
                    if isinstance(arg, StringLiteral):
                        return f'printf("%s\\n", {self._generate_expr(arg)})'
                    elif isinstance(arg, IntLiteral):
                        return f'printf("%d\\n", {self._generate_expr(arg)})'
                    else:
                        return f'printf("%s\\n", {self._generate_expr(arg)})'
                return 'printf("\\n")'
            elif func_name == "read":
                if expr.arguments:
                    arg = self._generate_expr(expr.arguments[0])
                    return f'scanf("%d", &{arg})'
                return 'scanf("%d", &__dummy)'
            
            return f"{func_name}({args})"
        
        elif isinstance(expr.callee, MemberExpr):
            # Method call through vtable
            member = expr.callee
            obj = self._generate_expr(member.obj)
            method_name = member.member
            
            # Use vtable for virtual dispatch
            return f"{obj}->__vtable->{method_name}({obj}{', ' + args if args else ''})"
        
        return f"/* unknown call */"
    
    def _generate_member_expr(self, expr: MemberExpr) -> str:
        """Generate a member access expression."""
        obj = self._generate_expr(expr.obj)
        return f"{obj}->{expr.member}"
    
    def _generate_new_expr(self, expr: NewExpr) -> str:
        """Generate a new expression (object creation)."""
        args = ", ".join(self._generate_expr(arg) for arg in expr.arguments)
        return f"{expr.class_name}_new({args})"
    
    def _generate_index_expr(self, expr: IndexExpr) -> str:
        """Generate an index expression."""
        obj = self._generate_expr(expr.obj)
        index = self._generate_expr(expr.index)
        return f"{obj}[{index}]"
    
    def _type_to_c(self, type_node: Optional[TypeNode]) -> str:
        """Convert a PPL type to a C type."""
        if type_node is None:
            return "void"
        
        type_map = {
            "int": "int",
            "float": "double",
            "bool": "bool",
            "char": "char",
            "string": "const char*",
            "void": "void"
        }
        
        base_type = type_map.get(type_node.name, f"{type_node.name}*")
        
        if type_node.is_array:
            return f"{base_type}*"
        
        return base_type
    
    def _infer_c_type(self, expr: Optional[Expr]) -> str:
        """Infer C type from an expression."""
        if expr is None:
            return "int"
        
        if isinstance(expr, IntLiteral):
            return "int"
        elif isinstance(expr, FloatLiteral):
            return "double"
        elif isinstance(expr, StringLiteral):
            return "const char*"
        elif isinstance(expr, CharLiteral):
            return "char"
        elif isinstance(expr, BoolLiteral):
            return "bool"
        elif isinstance(expr, NewExpr):
            return f"{expr.class_name}*"
        
        return "int"  # Default
    
    def _params_to_c(self, params: list[Parameter]) -> str:
        """Convert parameter list to C format."""
        if not params:
            return "void"
        
        parts = []
        for param in params:
            c_type = self._type_to_c(param.type_annotation)
            parts.append(f"{c_type} {param.name}")
        
        return ", ".join(parts)
    
    def _params_to_c_with_self(self, class_name: str, params: list[Parameter]) -> str:
        """Convert parameter list to C format with self pointer."""
        self_param = f"{class_name}* self"
        
        if not params:
            return self_param
        
        param_strs = [self_param]
        for param in params:
            c_type = self._type_to_c(param.type_annotation)
            param_strs.append(f"{c_type} {param.name}")
        
        return ", ".join(param_strs)


def generate(program: Program) -> str:
    """Generate C code from a program AST."""
    generator = CodeGenerator()
    return generator.generate(program)


def compile_and_run(c_code: str, output_file: str = None) -> tuple[bool, str]:
    """Compile C code using GCC and optionally run it."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(c_code)
        c_file = f.name
    
    if output_file is None:
        output_file = tempfile.mktemp(suffix='')
    
    try:
        # Compile with GCC
        result = subprocess.run(
            ['gcc', '-o', output_file, c_file, '-Wall'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False, f"Compilation failed:\n{result.stderr}"
        
        # Run the compiled program
        result = subprocess.run(
            [output_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout
        if result.returncode != 0:
            output += f"\nProgram exited with code {result.returncode}"
        
        return True, output
        
    except subprocess.TimeoutExpired:
        return False, "Execution timed out"
    except FileNotFoundError:
        return False, "GCC not found. Please install GCC."
    finally:
        # Cleanup
        if os.path.exists(c_file):
            os.unlink(c_file)
        if output_file and os.path.exists(output_file):
            os.unlink(output_file)
