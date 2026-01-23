"""AST Node definitions for the PPL language."""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto


class BinaryOp(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LEQ = auto()
    GT = auto()
    GEQ = auto()
    AND = auto()
    OR = auto()


class UnaryOp(Enum):
    NEG = auto()
    NOT = auto()


class AssignOp(Enum):
    ASSIGN = auto()
    ADD_ASSIGN = auto()
    SUB_ASSIGN = auto()
    MUL_ASSIGN = auto()
    DIV_ASSIGN = auto()
    MOD_ASSIGN = auto()


@dataclass
class SourceLocation:
    line: int
    column: int


# Base AST Node - use kw_only to allow derived classes to have required fields
@dataclass(kw_only=True)
class ASTNode:
    loc: Optional[SourceLocation] = None


# Type nodes
@dataclass(kw_only=True)
class TypeNode(ASTNode):
    name: str
    is_array: bool = False


# Expression nodes
@dataclass(kw_only=True)
class Expr(ASTNode):
    pass


@dataclass(kw_only=True)
class IntLiteral(Expr):
    value: int


@dataclass(kw_only=True)
class FloatLiteral(Expr):
    value: float


@dataclass(kw_only=True)
class StringLiteral(Expr):
    value: str


@dataclass(kw_only=True)
class CharLiteral(Expr):
    value: str


@dataclass(kw_only=True)
class BoolLiteral(Expr):
    value: bool


@dataclass(kw_only=True)
class Identifier(Expr):
    name: str


@dataclass(kw_only=True)
class BinaryExpr(Expr):
    left: Expr
    op: BinaryOp
    right: Expr


@dataclass(kw_only=True)
class UnaryExpr(Expr):
    op: UnaryOp
    operand: Expr


@dataclass(kw_only=True)
class CallExpr(Expr):
    callee: Expr
    arguments: list[Expr] = field(default_factory=list)


@dataclass(kw_only=True)
class MemberExpr(Expr):
    obj: Expr
    member: str
    is_private: bool = False


@dataclass(kw_only=True)
class NewExpr(Expr):
    class_name: str
    arguments: list[Expr] = field(default_factory=list)


@dataclass(kw_only=True)
class IndexExpr(Expr):
    obj: Expr
    index: Expr


# Statement nodes
@dataclass(kw_only=True)
class Stmt(ASTNode):
    pass


@dataclass(kw_only=True)
class ExprStmt(Stmt):
    expr: Expr


@dataclass(kw_only=True)
class VarDecl(Stmt):
    name: str
    type_annotation: Optional[TypeNode]
    initializer: Optional[Expr]
    is_private: bool = False


@dataclass(kw_only=True)
class Assignment(Stmt):
    target: Expr
    op: AssignOp
    value: Expr


@dataclass(kw_only=True)
class IfStmt(Stmt):
    condition: Expr
    then_branch: list[Stmt]
    else_branch: Optional[list[Stmt]] = None


@dataclass(kw_only=True)
class WhileStmt(Stmt):
    condition: Expr
    body: list[Stmt]


@dataclass(kw_only=True)
class ForStmt(Stmt):
    init: Optional[Stmt]
    condition: Optional[Expr]
    update: Optional[Stmt]
    body: list[Stmt]


@dataclass(kw_only=True)
class ReturnStmt(Stmt):
    value: Optional[Expr] = None


@dataclass(kw_only=True)
class BreakStmt(Stmt):
    pass


@dataclass(kw_only=True)
class ContinueStmt(Stmt):
    pass


@dataclass(kw_only=True)
class Block(Stmt):
    statements: list[Stmt]


# Parameter and function definitions
@dataclass(kw_only=True)
class Parameter(ASTNode):
    name: str
    type_annotation: TypeNode
    is_private: bool = False


@dataclass(kw_only=True)
class FunctionDecl(ASTNode):
    name: str
    params: list[Parameter]
    return_type: Optional[TypeNode]
    body: Optional[list[Stmt]]  # None for declarations without body
    is_private: bool = False
    is_override: bool = False


@dataclass(kw_only=True)
class FieldDecl(ASTNode):
    name: str
    type_annotation: TypeNode
    is_private: bool = False


@dataclass(kw_only=True)
class ClassDecl(ASTNode):
    name: str
    base_class: Optional[str]
    fields: list[FieldDecl]
    methods: list[FunctionDecl]


@dataclass(kw_only=True)
class Program(ASTNode):
    classes: list[ClassDecl]
    functions: list[FunctionDecl]
