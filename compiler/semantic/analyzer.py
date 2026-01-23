"""Semantic analyzer for the PPL language - performs type checking and name resolution."""
from dataclasses import dataclass, field
from typing import Optional
from compiler.parser.ast import (
    Program, ClassDecl, FunctionDecl, FieldDecl, Parameter, TypeNode,
    Stmt, VarDecl, Assignment, IfStmt, WhileStmt, ForStmt, ReturnStmt,
    BreakStmt, ContinueStmt, Block, ExprStmt, Expr, IntLiteral, FloatLiteral,
    StringLiteral, CharLiteral, BoolLiteral, Identifier, BinaryExpr,
    UnaryExpr, CallExpr, MemberExpr, NewExpr, IndexExpr, BinaryOp, UnaryOp, AssignOp
)


@dataclass
class SemanticError:
    message: str
    line: int
    column: int


@dataclass
class TypeInfo:
    """Represents type information for a value."""
    name: str
    is_array: bool = False
    
    def __eq__(self, other):
        if isinstance(other, TypeInfo):
            return self.name == other.name and self.is_array == other.is_array
        return False
    
    def __hash__(self):
        return hash((self.name, self.is_array))
    
    def is_numeric(self) -> bool:
        return self.name in ("int", "float") and not self.is_array
    
    def is_primitive(self) -> bool:
        return self.name in ("int", "float", "bool", "char", "string") and not self.is_array


# Built-in types
INT_TYPE = TypeInfo("int")
FLOAT_TYPE = TypeInfo("float")
BOOL_TYPE = TypeInfo("bool")
CHAR_TYPE = TypeInfo("char")
STRING_TYPE = TypeInfo("string")
VOID_TYPE = TypeInfo("void")


@dataclass
class Symbol:
    """Base class for symbol table entries."""
    name: str


@dataclass
class VarSymbol(Symbol):
    """Variable symbol."""
    type_info: TypeInfo
    is_private: bool = False


@dataclass
class FuncSymbol(Symbol):
    """Function symbol."""
    params: list[tuple[str, TypeInfo]]
    return_type: Optional[TypeInfo]
    is_private: bool = False
    is_override: bool = False
    is_method: bool = False


@dataclass
class ClassSymbol(Symbol):
    """Class symbol with fields and methods."""
    base_class: Optional[str] = None
    fields: dict[str, VarSymbol] = field(default_factory=dict)
    methods: dict[str, FuncSymbol] = field(default_factory=dict)


class Scope:
    """A scope containing symbols."""
    def __init__(self, parent: Optional['Scope'] = None):
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}
    
    def define(self, symbol: Symbol) -> bool:
        """Define a symbol in this scope. Returns False if already defined."""
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope and parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in this scope."""
        return self.symbols.get(name)


class SemanticAnalyzer:
    """Performs semantic analysis on the AST."""
    
    def __init__(self):
        self.errors: list[SemanticError] = []
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.current_class: Optional[ClassSymbol] = None
        self.current_function: Optional[FuncSymbol] = None
        self.loop_depth = 0
        
        # Register built-in functions
        self._register_builtins()
    
    def _register_builtins(self):
        """Register built-in functions."""
        # print function
        self.global_scope.define(FuncSymbol(
            name="print",
            params=[("value", STRING_TYPE)],
            return_type=VOID_TYPE
        ))
        # read function
        self.global_scope.define(FuncSymbol(
            name="read",
            params=[("var", INT_TYPE)],  # Note: this is simplified
            return_type=VOID_TYPE
        ))
    
    def error(self, message: str, node):
        """Report a semantic error."""
        line = node.loc.line if node.loc else 0
        col = node.loc.column if node.loc else 0
        self.errors.append(SemanticError(message, line, col))
    
    def enter_scope(self):
        """Enter a new scope."""
        self.current_scope = Scope(self.current_scope)
    
    def exit_scope(self):
        """Exit the current scope."""
        self.current_scope = self.current_scope.parent
    
    def type_node_to_info(self, type_node: Optional[TypeNode]) -> Optional[TypeInfo]:
        """Convert a TypeNode to TypeInfo."""
        if type_node is None:
            return None
        return TypeInfo(type_node.name, type_node.is_array)
    
    def analyze(self, program: Program) -> list[SemanticError]:
        """Analyze the entire program."""
        # First pass: register all classes and functions
        for cls in program.classes:
            self._register_class(cls)
        
        for func in program.functions:
            self._register_function(func)
        
        # Second pass: analyze class bodies
        for cls in program.classes:
            self._analyze_class(cls)
        
        # Third pass: analyze function bodies
        for func in program.functions:
            self._analyze_function(func)
        
        # Check for main function
        main_sym = self.global_scope.lookup("main")
        if not main_sym or not isinstance(main_sym, FuncSymbol):
            self.errors.append(SemanticError("No 'main' function defined", 0, 0))
        
        return self.errors
    
    def _register_class(self, cls: ClassDecl):
        """Register a class in the global scope."""
        if self.global_scope.lookup_local(cls.name):
            self.error(f"Class '{cls.name}' already defined", cls)
            return
        
        class_sym = ClassSymbol(name=cls.name, base_class=cls.base_class)
        
        # Register fields
        for field_decl in cls.fields:
            field_sym = VarSymbol(
                name=field_decl.name,
                type_info=self.type_node_to_info(field_decl.type_annotation),
                is_private=field_decl.is_private
            )
            class_sym.fields[field_decl.name] = field_sym
        
        # Register methods
        for method in cls.methods:
            params = [(p.name, self.type_node_to_info(p.type_annotation)) for p in method.params]
            method_sym = FuncSymbol(
                name=method.name,
                params=params,
                return_type=self.type_node_to_info(method.return_type),
                is_private=method.is_private,
                is_override=method.is_override,
                is_method=True
            )
            class_sym.methods[method.name] = method_sym
        
        self.global_scope.define(class_sym)
    
    def _register_function(self, func: FunctionDecl):
        """Register a function in the global scope."""
        if self.global_scope.lookup_local(func.name):
            self.error(f"Function '{func.name}' already defined", func)
            return
        
        params = [(p.name, self.type_node_to_info(p.type_annotation)) for p in func.params]
        func_sym = FuncSymbol(
            name=func.name,
            params=params,
            return_type=self.type_node_to_info(func.return_type),
            is_private=func.is_private
        )
        self.global_scope.define(func_sym)
    
    def _analyze_class(self, cls: ClassDecl):
        """Analyze a class definition."""
        class_sym = self.global_scope.lookup(cls.name)
        if not isinstance(class_sym, ClassSymbol):
            return
        
        # Check base class exists
        if cls.base_class:
            base = self.global_scope.lookup(cls.base_class)
            if not base or not isinstance(base, ClassSymbol):
                self.error(f"Base class '{cls.base_class}' not found", cls)
        
        self.current_class = class_sym
        
        # Analyze method bodies
        for method in cls.methods:
            if method.body:
                self._analyze_method(method, class_sym)
        
        self.current_class = None
    
    def _analyze_method(self, method: FunctionDecl, class_sym: ClassSymbol):
        """Analyze a method body."""
        self.enter_scope()
        
        # Add 'this' to scope (implicit)
        self.current_scope.define(VarSymbol("this", TypeInfo(class_sym.name)))
        
        # Add parameters to scope
        for param in method.params:
            param_type = self.type_node_to_info(param.type_annotation)
            self.current_scope.define(VarSymbol(param.name, param_type))
        
        method_sym = class_sym.methods.get(method.name)
        self.current_function = method_sym
        
        # Analyze body
        for stmt in method.body:
            self._analyze_stmt(stmt)
        
        self.current_function = None
        self.exit_scope()
    
    def _analyze_function(self, func: FunctionDecl):
        """Analyze a function body."""
        if not func.body:
            return
        
        func_sym = self.global_scope.lookup(func.name)
        if not isinstance(func_sym, FuncSymbol):
            return
        
        self.current_function = func_sym
        self.enter_scope()
        
        # Add parameters to scope
        for param in func.params:
            param_type = self.type_node_to_info(param.type_annotation)
            self.current_scope.define(VarSymbol(param.name, param_type))
        
        # Analyze body
        for stmt in func.body:
            self._analyze_stmt(stmt)
        
        self.exit_scope()
        self.current_function = None
    
    def _analyze_stmt(self, stmt: Stmt):
        """Analyze a statement."""
        if isinstance(stmt, VarDecl):
            self._analyze_var_decl(stmt)
        elif isinstance(stmt, Assignment):
            self._analyze_assignment(stmt)
        elif isinstance(stmt, IfStmt):
            self._analyze_if_stmt(stmt)
        elif isinstance(stmt, WhileStmt):
            self._analyze_while_stmt(stmt)
        elif isinstance(stmt, ForStmt):
            self._analyze_for_stmt(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._analyze_return_stmt(stmt)
        elif isinstance(stmt, BreakStmt):
            if self.loop_depth == 0:
                self.error("'break' outside of loop", stmt)
        elif isinstance(stmt, ContinueStmt):
            if self.loop_depth == 0:
                self.error("'continue' outside of loop", stmt)
        elif isinstance(stmt, Block):
            self.enter_scope()
            for s in stmt.statements:
                self._analyze_stmt(s)
            self.exit_scope()
        elif isinstance(stmt, ExprStmt):
            self._analyze_expr(stmt.expr)
    
    def _analyze_var_decl(self, stmt: VarDecl):
        """Analyze a variable declaration."""
        if self.current_scope.lookup_local(stmt.name):
            self.error(f"Variable '{stmt.name}' already defined in this scope", stmt)
            return
        
        var_type = None
        if stmt.type_annotation:
            var_type = self.type_node_to_info(stmt.type_annotation)
        
        if stmt.initializer:
            init_type = self._analyze_expr(stmt.initializer)
            if var_type is None:
                var_type = init_type
            elif init_type and not self._types_compatible(var_type, init_type):
                self.error(f"Type mismatch: cannot assign {init_type.name} to {var_type.name}", stmt)
        
        if var_type is None:
            self.error(f"Cannot infer type for variable '{stmt.name}'", stmt)
            var_type = TypeInfo("unknown")
        
        self.current_scope.define(VarSymbol(stmt.name, var_type))
    
    def _analyze_assignment(self, stmt: Assignment):
        """Analyze an assignment statement."""
        target_type = self._analyze_expr(stmt.target)
        value_type = self._analyze_expr(stmt.value)
        
        if target_type and value_type:
            if stmt.op != AssignOp.ASSIGN:
                # Compound assignment - check for numeric types
                if not target_type.is_numeric() or not value_type.is_numeric():
                    self.error(f"Compound assignment requires numeric types", stmt)
            elif not self._types_compatible(target_type, value_type):
                self.error(f"Type mismatch in assignment: {value_type.name} to {target_type.name}", stmt)
    
    def _analyze_if_stmt(self, stmt: IfStmt):
        """Analyze an if statement."""
        cond_type = self._analyze_expr(stmt.condition)
        if cond_type and cond_type != BOOL_TYPE and not cond_type.is_numeric():
            self.error("Condition must be a boolean or numeric expression", stmt)
        
        self.enter_scope()
        for s in stmt.then_branch:
            self._analyze_stmt(s)
        self.exit_scope()
        
        if stmt.else_branch:
            self.enter_scope()
            for s in stmt.else_branch:
                self._analyze_stmt(s)
            self.exit_scope()
    
    def _analyze_while_stmt(self, stmt: WhileStmt):
        """Analyze a while statement."""
        cond_type = self._analyze_expr(stmt.condition)
        if cond_type and cond_type != BOOL_TYPE and not cond_type.is_numeric():
            self.error("Condition must be a boolean or numeric expression", stmt)
        
        self.loop_depth += 1
        self.enter_scope()
        for s in stmt.body:
            self._analyze_stmt(s)
        self.exit_scope()
        self.loop_depth -= 1
    
    def _analyze_for_stmt(self, stmt: ForStmt):
        """Analyze a for statement."""
        self.enter_scope()
        
        if stmt.init:
            self._analyze_stmt(stmt.init)
        
        if stmt.condition:
            cond_type = self._analyze_expr(stmt.condition)
            if cond_type and cond_type != BOOL_TYPE and not cond_type.is_numeric():
                self.error("Condition must be a boolean or numeric expression", stmt)
        
        self.loop_depth += 1
        for s in stmt.body:
            self._analyze_stmt(s)
        self.loop_depth -= 1
        
        if stmt.update:
            self._analyze_stmt(stmt.update)
        
        self.exit_scope()
    
    def _analyze_return_stmt(self, stmt: ReturnStmt):
        """Analyze a return statement."""
        if not self.current_function:
            self.error("'return' outside of function", stmt)
            return
        
        expected_type = self.current_function.return_type
        
        if stmt.value:
            actual_type = self._analyze_expr(stmt.value)
            if expected_type and actual_type and not self._types_compatible(expected_type, actual_type):
                self.error(f"Return type mismatch: expected {expected_type.name}, got {actual_type.name}", stmt)
        elif expected_type and expected_type != VOID_TYPE:
            self.error(f"Expected return value of type {expected_type.name}", stmt)
    
    def _analyze_expr(self, expr: Expr) -> Optional[TypeInfo]:
        """Analyze an expression and return its type."""
        if isinstance(expr, IntLiteral):
            return INT_TYPE
        elif isinstance(expr, FloatLiteral):
            return FLOAT_TYPE
        elif isinstance(expr, StringLiteral):
            return STRING_TYPE
        elif isinstance(expr, CharLiteral):
            return CHAR_TYPE
        elif isinstance(expr, BoolLiteral):
            return BOOL_TYPE
        elif isinstance(expr, Identifier):
            return self._analyze_identifier(expr)
        elif isinstance(expr, BinaryExpr):
            return self._analyze_binary_expr(expr)
        elif isinstance(expr, UnaryExpr):
            return self._analyze_unary_expr(expr)
        elif isinstance(expr, CallExpr):
            return self._analyze_call_expr(expr)
        elif isinstance(expr, MemberExpr):
            return self._analyze_member_expr(expr)
        elif isinstance(expr, NewExpr):
            return self._analyze_new_expr(expr)
        elif isinstance(expr, IndexExpr):
            return self._analyze_index_expr(expr)
        
        return None
    
    def _analyze_identifier(self, expr: Identifier) -> Optional[TypeInfo]:
        """Analyze an identifier reference."""
        symbol = self.current_scope.lookup(expr.name)
        if symbol is None:
            self.error(f"Undefined variable '{expr.name}'", expr)
            return None
        
        if isinstance(symbol, VarSymbol):
            return symbol.type_info
        elif isinstance(symbol, FuncSymbol):
            # Function reference (for passing as argument, etc.)
            return TypeInfo("function")
        
        return None
    
    def _analyze_binary_expr(self, expr: BinaryExpr) -> Optional[TypeInfo]:
        """Analyze a binary expression."""
        left_type = self._analyze_expr(expr.left)
        right_type = self._analyze_expr(expr.right)
        
        if left_type is None or right_type is None:
            return None
        
        if expr.op in (BinaryOp.ADD, BinaryOp.SUB, BinaryOp.MUL, BinaryOp.DIV, BinaryOp.MOD):
            if not left_type.is_numeric() or not right_type.is_numeric():
                self.error(f"Arithmetic operators require numeric operands", expr)
                return None
            # Promote to float if either operand is float
            if left_type == FLOAT_TYPE or right_type == FLOAT_TYPE:
                return FLOAT_TYPE
            return INT_TYPE
        
        elif expr.op in (BinaryOp.EQ, BinaryOp.NEQ):
            if not self._types_compatible(left_type, right_type):
                self.error(f"Cannot compare {left_type.name} with {right_type.name}", expr)
            return BOOL_TYPE
        
        elif expr.op in (BinaryOp.LT, BinaryOp.LEQ, BinaryOp.GT, BinaryOp.GEQ):
            if not left_type.is_numeric() or not right_type.is_numeric():
                self.error(f"Comparison operators require numeric operands", expr)
            return BOOL_TYPE
        
        elif expr.op in (BinaryOp.AND, BinaryOp.OR):
            if left_type != BOOL_TYPE or right_type != BOOL_TYPE:
                # Allow numeric types for logical operations (C-style)
                if not (left_type.is_numeric() or left_type == BOOL_TYPE):
                    self.error(f"Logical operators require boolean operands", expr)
                if not (right_type.is_numeric() or right_type == BOOL_TYPE):
                    self.error(f"Logical operators require boolean operands", expr)
            return BOOL_TYPE
        
        return None
    
    def _analyze_unary_expr(self, expr: UnaryExpr) -> Optional[TypeInfo]:
        """Analyze a unary expression."""
        operand_type = self._analyze_expr(expr.operand)
        
        if operand_type is None:
            return None
        
        if expr.op == UnaryOp.NEG:
            if not operand_type.is_numeric():
                self.error(f"Negation requires numeric operand", expr)
            return operand_type
        
        elif expr.op == UnaryOp.NOT:
            if operand_type != BOOL_TYPE and not operand_type.is_numeric():
                self.error(f"Logical not requires boolean operand", expr)
            return BOOL_TYPE
        
        return None
    
    def _analyze_call_expr(self, expr: CallExpr) -> Optional[TypeInfo]:
        """Analyze a function call expression."""
        if isinstance(expr.callee, Identifier):
            func_name = expr.callee.name
            symbol = self.current_scope.lookup(func_name)
            
            if symbol is None:
                self.error(f"Undefined function '{func_name}'", expr)
                return None
            
            if not isinstance(symbol, FuncSymbol):
                self.error(f"'{func_name}' is not a function", expr)
                return None
            
            # Check argument count
            if len(expr.arguments) != len(symbol.params):
                self.error(f"Function '{func_name}' expects {len(symbol.params)} arguments, got {len(expr.arguments)}", expr)
            
            # Check argument types
            for i, (arg, (param_name, param_type)) in enumerate(zip(expr.arguments, symbol.params)):
                arg_type = self._analyze_expr(arg)
                if arg_type and param_type and not self._types_compatible(param_type, arg_type):
                    self.error(f"Argument {i+1} type mismatch: expected {param_type.name}, got {arg_type.name}", expr)
            
            return symbol.return_type
        
        elif isinstance(expr.callee, MemberExpr):
            return self._analyze_method_call(expr)
        
        return None
    
    def _analyze_method_call(self, expr: CallExpr) -> Optional[TypeInfo]:
        """Analyze a method call on an object."""
        member_expr = expr.callee
        obj_type = self._analyze_expr(member_expr.obj)
        
        if obj_type is None:
            return None
        
        class_sym = self.global_scope.lookup(obj_type.name)
        if not isinstance(class_sym, ClassSymbol):
            self.error(f"Type '{obj_type.name}' has no methods", expr)
            return None
        
        method_name = member_expr.member
        method_sym = class_sym.methods.get(method_name)
        
        if method_sym is None:
            # Check base class
            if class_sym.base_class:
                base_sym = self.global_scope.lookup(class_sym.base_class)
                if isinstance(base_sym, ClassSymbol):
                    method_sym = base_sym.methods.get(method_name)
        
        if method_sym is None:
            self.error(f"Method '{method_name}' not found in class '{obj_type.name}'", expr)
            return None
        
        # Check private access
        if method_sym.is_private and self.current_class != class_sym:
            self.error(f"Cannot access private method '{method_name}'", expr)
        
        # Check arguments
        if len(expr.arguments) != len(method_sym.params):
            self.error(f"Method '{method_name}' expects {len(method_sym.params)} arguments", expr)
        
        return method_sym.return_type
    
    def _analyze_member_expr(self, expr: MemberExpr) -> Optional[TypeInfo]:
        """Analyze a member access expression."""
        obj_type = self._analyze_expr(expr.obj)
        
        if obj_type is None:
            return None
        
        class_sym = self.global_scope.lookup(obj_type.name)
        if not isinstance(class_sym, ClassSymbol):
            self.error(f"Type '{obj_type.name}' has no members", expr)
            return None
        
        field_sym = class_sym.fields.get(expr.member)
        if field_sym is None:
            self.error(f"Field '{expr.member}' not found in class '{obj_type.name}'", expr)
            return None
        
        # Check private access
        if field_sym.is_private and self.current_class != class_sym:
            self.error(f"Cannot access private field '{expr.member}'", expr)
        
        return field_sym.type_info
    
    def _analyze_new_expr(self, expr: NewExpr) -> Optional[TypeInfo]:
        """Analyze a new expression (object creation)."""
        class_sym = self.global_scope.lookup(expr.class_name)
        
        if class_sym is None:
            self.error(f"Undefined class '{expr.class_name}'", expr)
            return None
        
        if not isinstance(class_sym, ClassSymbol):
            self.error(f"'{expr.class_name}' is not a class", expr)
            return None
        
        # Check for constructor
        constructor = class_sym.methods.get(expr.class_name)
        if constructor:
            if len(expr.arguments) != len(constructor.params):
                self.error(f"Constructor expects {len(constructor.params)} arguments", expr)
        
        return TypeInfo(expr.class_name)
    
    def _analyze_index_expr(self, expr: IndexExpr) -> Optional[TypeInfo]:
        """Analyze an index expression (array access)."""
        obj_type = self._analyze_expr(expr.obj)
        index_type = self._analyze_expr(expr.index)
        
        if obj_type is None:
            return None
        
        if not obj_type.is_array:
            self.error(f"Cannot index non-array type '{obj_type.name}'", expr)
            return None
        
        if index_type and index_type != INT_TYPE:
            self.error(f"Array index must be integer", expr)
        
        return TypeInfo(obj_type.name, is_array=False)
    
    def _types_compatible(self, expected: TypeInfo, actual: TypeInfo) -> bool:
        """Check if actual type is compatible with expected type."""
        if expected == actual:
            return True
        
        # Allow int to float conversion
        if expected == FLOAT_TYPE and actual == INT_TYPE:
            return True
        
        # Check class inheritance
        if not expected.is_primitive() and not actual.is_primitive():
            actual_class = self.global_scope.lookup(actual.name)
            if isinstance(actual_class, ClassSymbol):
                while actual_class:
                    if actual_class.name == expected.name:
                        return True
                    if actual_class.base_class:
                        actual_class = self.global_scope.lookup(actual_class.base_class)
                        if not isinstance(actual_class, ClassSymbol):
                            break
                    else:
                        break
        
        return False


def analyze(program: Program) -> list[SemanticError]:
    """Analyze a program and return any semantic errors."""
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
