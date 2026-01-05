from enum import Enum, auto
from dataclasses import dataclass

class TokenKind(Enum):
    EOF = -1
    IDENTIFIER = auto()
    INTEGER_CONSTANT = auto()
    FLOAT_CONSTANT = auto()
    STRING_CONSTANT = auto()

    KW_FN = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_CLASS = auto()
    KW_NEW = auto()
    KW_RETURN = auto()
    KW_WHILE = auto()
    KW_FOR = auto()
    KW_BREAK = auto()
    KW_CONTINUE = auto()

    OP_ANDAND = auto()
    OP_OROR = auto()
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_MULTIPLY = auto()
    OP_DIVIDE = auto()
    OP_MODULO = auto()
    OP_PLUSEQ = auto()
    OP_MINUSEQ = auto()
    OP_MULTIPLYEQ = auto()
    OP_DIVIDEEQ = auto()
    OP_MODULOEQ = auto()
    OP_LESS = auto()
    OP_LEQ = auto()
    OP_GREATER = auto()
    OP_GEQ = auto()
    OP_NOT = auto()
    OP_EQUALEQUAL = auto()
    OP_NOTEQUAL = auto()

    EQUAL = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COLON = auto()
    COMMA = auto()

@dataclass
class Token:
    kind: TokenKind
    linenum: int
    column: int
    value: str = ""

    def eof(self):
        return self.kind == TokenKind.EOF
    
keywords = {
    kw[3:].lower(): getattr(TokenKind, kw) for kw in dir(TokenKind) if kw.startswith("KW_")
}

def keyword_or_identifier(s):
    return keywords.get(s, TokenKind.IDENTIFIER)

class Lexer:
    def __init__(self, _input: str):
        self.input = _input
        self.ptr = 0
        self.linenum = 0
        self.column = 0

    def done(self):
        return self.ptr >= len(self.input)
    
    def consume(self):
        self.column += 1
        c = self.peek()
        self.ptr += 1
        return c
    
    def try_eat(self, c):
        assert len(c) == 1
        if not self.done() and self.input[self.ptr] == c:
            assert self.consume() == c
            return True
        return False
    
    def peek(self):
        assert not self.done()
        return self.input[self.ptr]
    
    def tokener(self):
        linenum = self.linenum
        column = self.column
        def _(kind, value=""):
            return Token(kind, linenum, column, value)
        return _
    
    # return one token or eof if end of file
    def lex(self):
        while self.ptr < len(self.input):
            tokener = self.tokener()
            c = self.consume()

            match c:
                case _ if 'a' <= c <= 'z' or 'A' <= c <= 'Z':
                    value = c
                    while not self.done() and self.peek().isalnum():
                        value += self.consume()

                    return tokener(keyword_or_identifier(value), value)
                
                case '+':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_PLUSEQ, '+=')
                    return tokener(TokenKind.OP_PLUS, '+')
                
                case '-':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_MINUSEQ, '-=')
                    return tokener(TokenKind.OP_MINUS, '-')
                
                case '*':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_MULTIPLYEQ, '*=')
                    return tokener(TokenKind.OP_MULTIPLY, '*')
                
                case '/':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_DIVIDEEQ, '/=')
                    return tokener(TokenKind.OP_DIVIDE, '-')
                
                case '%':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_MODULOEQ, '%=')
                    return tokener(TokenKind.OP_MODULO, '%')
                
                case '=':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_EQUALEQUAL, '==')
                    return tokener(TokenKind.EQUAL, '=')
                
                case '<':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_LEQ, '<=')
                    return tokener(TokenKind.OP_LESS, '<')
                
                case '>':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_GEQ, '>=')
                    return tokener(TokenKind.OP_GREATER, '>')
                
                case '!':
                    if self.try_eat('='):
                        return tokener(TokenKind.OP_NOTEQUAL, '!=')
                    return tokener(TokenKind.OP_NOT, '!')
                
                case _ if '0' <= c <= '9':
                    value = c
                    while not self.done() and self.peek().isdigit():
                        value += self.consume()
                    
                    if self.try_eat('.'): #float constant
                        value += '.'
                        while not self.done() and self.peek().isdigit():
                            value += self.consume()
                        return tokener(TokenKind.FLOAT_CONSTANT, value)
                    else:
                        return tokener(TokenKind.INTEGER_CONSTANT, value)

                case '"':
                    value = c
                    while not self.done() and self.peek() != '\n':
                        if self.try_eat('\\'): #skip escaped character
                            value += '\\' + self.consume()
                            continue
                        value += self.consume()
                        if value[-1] == '"':
                            break
                    
                    return tokener(TokenKind.STRING_CONSTANT, value)
                case '\n':
                    self.linenum += 1
                    self.column = 0
                    pass

        return Token(TokenKind.EOF, -1, -1)

if __name__ == "__main__":
    s = """fn fn fn fn
    if 
    else 11203 1.1231231123 0.12013 "asdasdsadasdsad"
    """

    l = Lexer(s)

    while not (tok := l.lex()).eof():
        print(tok)