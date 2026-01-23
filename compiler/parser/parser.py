"""Parser for the PPL language using recursive descent."""
from typing import Optional
from compiler.lexer.lexer import Lexer, Token, TokenKind
from compiler.parser.ast import (
    ASTNode, SourceLocation, TypeNode, Expr, IntLiteral, FloatLiteral,
    StringLiteral, CharLiteral, BoolLiteral, Identifier, BinaryExpr,
    UnaryExpr, CallExpr, MemberExpr, NewExpr, IndexExpr, Stmt, ExprStmt,
    VarDecl, Assignment, IfStmt, WhileStmt, ForStmt, ReturnStmt, BreakStmt,
    ContinueStmt, Block, Parameter, FunctionDecl, FieldDecl, ClassDecl,
    Program, BinaryOp, UnaryOp, AssignOp
)


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.token = token
        self.message = message


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current: Token = self.lexer.lex()
        self.errors: list[ParseError] = []

    def loc(self) -> SourceLocation:
        return SourceLocation(self.current.linenum, self.current.column)

    def advance(self) -> Token:
        prev = self.current
        self.current = self.lexer.lex()
        return prev

    def check(self, kind: TokenKind) -> bool:
        return self.current.kind == kind

    def match(self, *kinds: TokenKind) -> Optional[Token]:
        for kind in kinds:
            if self.check(kind):
                return self.advance()
        return None

    def expect(self, kind: TokenKind, message: str) -> Token:
        if self.check(kind):
            return self.advance()
        raise ParseError(f"{message}, got {self.current.kind.name}", self.current)

    def synchronize(self):
        """Recover from parse error by advancing to a synchronization point."""
        self.advance()
        while not self.check(TokenKind.EOF):
            if self.current.kind in (TokenKind.KW_CLASS, TokenKind.KW_FN, 
                                      TokenKind.KW_LET, TokenKind.KW_IF,
                                      TokenKind.KW_WHILE, TokenKind.KW_FOR,
                                      TokenKind.KW_RETURN):
                return
            self.advance()

    def parse(self) -> Program:
        """Parse the entire program."""
        classes = []
        functions = []
        
        while not self.check(TokenKind.EOF):
            try:
                if self.check(TokenKind.KW_CLASS):
                    classes.append(self.parse_class_decl())
                elif self.check(TokenKind.KW_FN):
                    functions.append(self.parse_function_decl())
                else:
                    raise ParseError(f"Expected class or function declaration", self.current)
            except ParseError as e:
                self.errors.append(e)
                self.synchronize()
        
        return Program(classes=classes, functions=functions, loc=SourceLocation(1, 1))

    def parse_class_decl(self) -> ClassDecl:
        """Parse: class Name [: BaseClass] { fields and methods }"""
        loc = self.loc()
        self.expect(TokenKind.KW_CLASS, "Expected 'class'")
        name = self.expect(TokenKind.IDENTIFIER, "Expected class name").value
        
        base_class = None
        if self.match(TokenKind.COLON):
            base_class = self.expect(TokenKind.IDENTIFIER, "Expected base class name").value
        
        self.expect(TokenKind.LBRACE, "Expected '{' after class declaration")
        
        fields = []
        methods = []
        
        while not self.check(TokenKind.RBRACE) and not self.check(TokenKind.EOF):
            is_private = self.match(TokenKind.HASH) is not None
            
            if self.check(TokenKind.KW_FN):
                method = self.parse_function_decl(is_member=True, already_private=is_private)
                methods.append(method)
            else:
                field = self.parse_field_decl(is_private)
                fields.append(field)
        
        self.expect(TokenKind.RBRACE, "Expected '}' after class body")
        
        return ClassDecl(name=name, base_class=base_class, fields=fields, methods=methods, loc=loc)

    def parse_field_decl(self, is_private: bool = False) -> FieldDecl:
        """Parse: [#] name: type"""
        loc = self.loc()
        name = self.expect(TokenKind.IDENTIFIER, "Expected field name").value
        self.expect(TokenKind.COLON, "Expected ':' after field name")
        type_ann = self.parse_type()
        
        return FieldDecl(name=name, type_annotation=type_ann, is_private=is_private, loc=loc)

    def parse_function_decl(self, is_member: bool = False, already_private: bool = False) -> FunctionDecl:
        """Parse: fn [#] [!] Name(params): ReturnType [{ body }]"""
        loc = self.loc()
        self.expect(TokenKind.KW_FN, "Expected 'fn'")
        
        is_private = already_private or self.match(TokenKind.HASH) is not None
        is_override = self.match(TokenKind.OP_NOT) is not None
        
        name = self.expect(TokenKind.IDENTIFIER, "Expected function name").value
        
        self.expect(TokenKind.LPAREN, "Expected '(' after function name")
        params = self.parse_parameter_list()
        self.expect(TokenKind.RPAREN, "Expected ')' after parameters")
        
        return_type = None
        if self.match(TokenKind.COLON):
            return_type = self.parse_type()
        
        body = None
        if self.check(TokenKind.LBRACE):
            body = self.parse_block()
        
        return FunctionDecl(
            name=name, params=params, return_type=return_type,
            body=body, is_private=is_private, is_override=is_override, loc=loc
        )

    def parse_parameter_list(self) -> list[Parameter]:
        """Parse comma-separated parameter list."""
        params = []
        
        if not self.check(TokenKind.RPAREN):
            params.append(self.parse_parameter())
            while self.match(TokenKind.COMMA):
                params.append(self.parse_parameter())
        
        return params

    def parse_parameter(self) -> Parameter:
        """Parse: name: type"""
        loc = self.loc()
        name = self.expect(TokenKind.IDENTIFIER, "Expected parameter name").value
        self.expect(TokenKind.COLON, "Expected ':' after parameter name")
        type_ann = self.parse_type()
        
        return Parameter(name=name, type_annotation=type_ann, loc=loc)

    def parse_type(self) -> TypeNode:
        """Parse a type annotation (int, string, float, char, bool, or class name)."""
        loc = self.loc()
        
        if self.match(TokenKind.KW_INT):
            name = "int"
        elif self.match(TokenKind.KW_STRING):
            name = "string"
        elif self.match(TokenKind.KW_FLOAT):
            name = "float"
        elif self.match(TokenKind.KW_CHAR):
            name = "char"
        elif self.match(TokenKind.KW_BOOL):
            name = "bool"
        elif self.check(TokenKind.IDENTIFIER):
            name = self.advance().value
        else:
            raise ParseError("Expected type name", self.current)
        
        is_array = False
        if self.match(TokenKind.LBRACKET):
            self.expect(TokenKind.RBRACKET, "Expected ']' after '['")
            is_array = True
        
        return TypeNode(name=name, is_array=is_array, loc=loc)

    def parse_block(self) -> list[Stmt]:
        """Parse: { statements }"""
        self.expect(TokenKind.LBRACE, "Expected '{'")
        
        statements = []
        while not self.check(TokenKind.RBRACE) and not self.check(TokenKind.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        self.expect(TokenKind.RBRACE, "Expected '}'")
        return statements

    def parse_statement(self) -> Optional[Stmt]:
        """Parse a single statement."""
        if self.check(TokenKind.KW_LET):
            return self.parse_var_decl()
        elif self.check(TokenKind.KW_IF):
            return self.parse_if_stmt()
        elif self.check(TokenKind.KW_WHILE):
            return self.parse_while_stmt()
        elif self.check(TokenKind.KW_FOR):
            return self.parse_for_stmt()
        elif self.check(TokenKind.KW_RETURN):
            return self.parse_return_stmt()
        elif self.check(TokenKind.KW_BREAK):
            loc = self.loc()
            self.advance()
            self.match(TokenKind.SEMICOLON)
            return BreakStmt(loc=loc)
        elif self.check(TokenKind.KW_CONTINUE):
            loc = self.loc()
            self.advance()
            self.match(TokenKind.SEMICOLON)
            return ContinueStmt(loc=loc)
        elif self.check(TokenKind.LBRACE):
            return Block(statements=self.parse_block(), loc=self.loc())
        else:
            return self.parse_expr_or_assignment_stmt()

    def parse_var_decl(self) -> VarDecl:
        """Parse: let name [: type] [= expr]"""
        loc = self.loc()
        self.expect(TokenKind.KW_LET, "Expected 'let'")
        
        name = self.expect(TokenKind.IDENTIFIER, "Expected variable name").value
        
        type_annotation = None
        if self.match(TokenKind.COLON):
            type_annotation = self.parse_type()
        
        initializer = None
        if self.match(TokenKind.EQUAL):
            initializer = self.parse_expression()
        
        self.match(TokenKind.SEMICOLON)
        
        return VarDecl(name=name, type_annotation=type_annotation, initializer=initializer, loc=loc)

    def parse_if_stmt(self) -> IfStmt:
        """Parse: if condition { body } [else { body }]"""
        loc = self.loc()
        self.expect(TokenKind.KW_IF, "Expected 'if'")
        
        condition = self.parse_expression()
        then_branch = self.parse_block()
        
        else_branch = None
        if self.match(TokenKind.KW_ELSE):
            if self.check(TokenKind.KW_IF):
                else_branch = [self.parse_if_stmt()]
            else:
                else_branch = self.parse_block()
        
        return IfStmt(condition=condition, then_branch=then_branch, else_branch=else_branch, loc=loc)

    def parse_while_stmt(self) -> WhileStmt:
        """Parse: while condition { body }"""
        loc = self.loc()
        self.expect(TokenKind.KW_WHILE, "Expected 'while'")
        
        condition = self.parse_expression()
        body = self.parse_block()
        
        return WhileStmt(condition=condition, body=body, loc=loc)

    def parse_for_stmt(self) -> ForStmt:
        """Parse: for init; condition; update { body }"""
        loc = self.loc()
        self.expect(TokenKind.KW_FOR, "Expected 'for'")
        
        init = None
        if not self.check(TokenKind.SEMICOLON):
            if self.check(TokenKind.KW_LET):
                init = self.parse_var_decl()
            else:
                init = self.parse_expr_or_assignment_stmt()
        else:
            self.advance()  # consume semicolon
        
        condition = None
        if not self.check(TokenKind.SEMICOLON):
            condition = self.parse_expression()
        self.expect(TokenKind.SEMICOLON, "Expected ';' after for condition")
        
        update = None
        if not self.check(TokenKind.LBRACE):
            update = self.parse_expr_or_assignment_stmt()
        
        body = self.parse_block()
        
        return ForStmt(init=init, condition=condition, update=update, body=body, loc=loc)

    def parse_return_stmt(self) -> ReturnStmt:
        """Parse: return [expr]"""
        loc = self.loc()
        self.expect(TokenKind.KW_RETURN, "Expected 'return'")
        
        value = None
        if not self.check(TokenKind.SEMICOLON) and not self.check(TokenKind.RBRACE):
            value = self.parse_expression()
        
        self.match(TokenKind.SEMICOLON)
        
        return ReturnStmt(value=value, loc=loc)

    def parse_expr_or_assignment_stmt(self) -> Stmt:
        """Parse expression or assignment statement."""
        loc = self.loc()
        expr = self.parse_expression()
        
        # Check for assignment operators
        op = None
        if self.match(TokenKind.EQUAL):
            op = AssignOp.ASSIGN
        elif self.match(TokenKind.OP_PLUSEQ):
            op = AssignOp.ADD_ASSIGN
        elif self.match(TokenKind.OP_MINUSEQ):
            op = AssignOp.SUB_ASSIGN
        elif self.match(TokenKind.OP_MULTIPLYEQ):
            op = AssignOp.MUL_ASSIGN
        elif self.match(TokenKind.OP_DIVIDEEQ):
            op = AssignOp.DIV_ASSIGN
        elif self.match(TokenKind.OP_MODULOEQ):
            op = AssignOp.MOD_ASSIGN
        
        if op is not None:
            value = self.parse_expression()
            self.match(TokenKind.SEMICOLON)
            return Assignment(target=expr, op=op, value=value, loc=loc)
        
        self.match(TokenKind.SEMICOLON)
        return ExprStmt(expr=expr, loc=loc)

    # Expression parsing using precedence climbing
    def parse_expression(self) -> Expr:
        return self.parse_or_expr()

    def parse_or_expr(self) -> Expr:
        left = self.parse_and_expr()
        
        while self.match(TokenKind.OP_OROR):
            right = self.parse_and_expr()
            left = BinaryExpr(left=left, op=BinaryOp.OR, right=right, loc=left.loc)
        
        return left

    def parse_and_expr(self) -> Expr:
        left = self.parse_equality_expr()
        
        while self.match(TokenKind.OP_ANDAND):
            right = self.parse_equality_expr()
            left = BinaryExpr(left=left, op=BinaryOp.AND, right=right, loc=left.loc)
        
        return left

    def parse_equality_expr(self) -> Expr:
        left = self.parse_relational_expr()
        
        while True:
            if self.match(TokenKind.OP_EQUALEQUAL):
                right = self.parse_relational_expr()
                left = BinaryExpr(left=left, op=BinaryOp.EQ, right=right, loc=left.loc)
            elif self.match(TokenKind.OP_NOTEQUAL):
                right = self.parse_relational_expr()
                left = BinaryExpr(left=left, op=BinaryOp.NEQ, right=right, loc=left.loc)
            else:
                break
        
        return left

    def parse_relational_expr(self) -> Expr:
        left = self.parse_additive_expr()
        
        while True:
            if self.match(TokenKind.OP_LESS):
                right = self.parse_additive_expr()
                left = BinaryExpr(left=left, op=BinaryOp.LT, right=right, loc=left.loc)
            elif self.match(TokenKind.OP_LEQ):
                right = self.parse_additive_expr()
                left = BinaryExpr(left=left, op=BinaryOp.LEQ, right=right, loc=left.loc)
            elif self.match(TokenKind.OP_GREATER):
                right = self.parse_additive_expr()
                left = BinaryExpr(left=left, op=BinaryOp.GT, right=right, loc=left.loc)
            elif self.match(TokenKind.OP_GEQ):
                right = self.parse_additive_expr()
                left = BinaryExpr(left=left, op=BinaryOp.GEQ, right=right, loc=left.loc)
            else:
                break
        
        return left

    def parse_additive_expr(self) -> Expr:
        left = self.parse_multiplicative_expr()
        
        while True:
            if self.match(TokenKind.OP_PLUS):
                right = self.parse_multiplicative_expr()
                left = BinaryExpr(left=left, op=BinaryOp.ADD, right=right, loc=left.loc)
            elif self.match(TokenKind.OP_MINUS):
                right = self.parse_multiplicative_expr()
                left = BinaryExpr(left=left, op=BinaryOp.SUB, right=right, loc=left.loc)
            else:
                break
        
        return left

    def parse_multiplicative_expr(self) -> Expr:
        left = self.parse_unary_expr()
        
        while True:
            if self.match(TokenKind.OP_MULTIPLY):
                right = self.parse_unary_expr()
                left = BinaryExpr(left=left, op=BinaryOp.MUL, right=right, loc=left.loc)
            elif self.match(TokenKind.OP_DIVIDE):
                right = self.parse_unary_expr()
                left = BinaryExpr(left=left, op=BinaryOp.DIV, right=right, loc=left.loc)
            elif self.match(TokenKind.OP_MODULO):
                right = self.parse_unary_expr()
                left = BinaryExpr(left=left, op=BinaryOp.MOD, right=right, loc=left.loc)
            else:
                break
        
        return left

    def parse_unary_expr(self) -> Expr:
        loc = self.loc()
        
        if self.match(TokenKind.OP_MINUS):
            operand = self.parse_unary_expr()
            return UnaryExpr(op=UnaryOp.NEG, operand=operand, loc=loc)
        elif self.match(TokenKind.OP_NOT):
            operand = self.parse_unary_expr()
            return UnaryExpr(op=UnaryOp.NOT, operand=operand, loc=loc)
        
        return self.parse_postfix_expr()

    def parse_postfix_expr(self) -> Expr:
        expr = self.parse_primary_expr()
        
        while True:
            if self.match(TokenKind.DOT):
                is_private = self.match(TokenKind.HASH) is not None
                member = self.expect(TokenKind.IDENTIFIER, "Expected member name").value
                expr = MemberExpr(obj=expr, member=member, is_private=is_private, loc=expr.loc)
            elif self.match(TokenKind.LPAREN):
                args = self.parse_argument_list()
                self.expect(TokenKind.RPAREN, "Expected ')' after arguments")
                expr = CallExpr(callee=expr, arguments=args, loc=expr.loc)
            elif self.match(TokenKind.LBRACKET):
                index = self.parse_expression()
                self.expect(TokenKind.RBRACKET, "Expected ']' after index")
                expr = IndexExpr(obj=expr, index=index, loc=expr.loc)
            else:
                break
        
        return expr

    def parse_argument_list(self) -> list[Expr]:
        args = []
        
        if not self.check(TokenKind.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenKind.COMMA):
                args.append(self.parse_expression())
        
        return args

    def parse_primary_expr(self) -> Expr:
        loc = self.loc()
        tok = self.current
        
        if tok.kind == TokenKind.INTEGER_CONSTANT:
            self.advance()
            return IntLiteral(value=int(tok.value), loc=loc)
        elif tok.kind == TokenKind.FLOAT_CONSTANT:
            self.advance()
            return FloatLiteral(value=float(tok.value), loc=loc)
        elif tok.kind == TokenKind.STRING_CONSTANT:
            self.advance()
            return StringLiteral(value=tok.value, loc=loc)
        elif tok.kind == TokenKind.CHAR_CONSTANT:
            self.advance()
            return CharLiteral(value=tok.value, loc=loc)
        elif tok.kind == TokenKind.KW_TRUE:
            self.advance()
            return BoolLiteral(value=True, loc=loc)
        elif tok.kind == TokenKind.KW_FALSE:
            self.advance()
            return BoolLiteral(value=False, loc=loc)
        elif tok.kind == TokenKind.IDENTIFIER:
            self.advance()
            return Identifier(name=tok.value, loc=loc)
        elif tok.kind == TokenKind.KW_NEW:
            return self.parse_new_expr()
        elif self.match(TokenKind.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenKind.RPAREN, "Expected ')' after expression")
            return expr
        else:
            raise ParseError(f"Unexpected token in expression: {tok.kind.name}", tok)

    def parse_new_expr(self) -> NewExpr:
        """Parse: new ClassName(args)"""
        loc = self.loc()
        self.expect(TokenKind.KW_NEW, "Expected 'new'")
        class_name = self.expect(TokenKind.IDENTIFIER, "Expected class name").value
        
        self.expect(TokenKind.LPAREN, "Expected '(' after class name")
        args = self.parse_argument_list()
        self.expect(TokenKind.RPAREN, "Expected ')' after arguments")
        
        return NewExpr(class_name=class_name, arguments=args, loc=loc)


def parse(source: str) -> tuple[Program, list[ParseError]]:
    """Parse source code and return AST and any errors."""
    lexer = Lexer(source)
    parser = Parser(lexer)
    return parser.parse(), parser.errors
