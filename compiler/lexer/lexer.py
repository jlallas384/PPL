from enum import Enum, auto
from dataclasses import dataclass
import sys
from tabulate import tabulate

class TokenKind(Enum):
    EOF = -1
    IDENTIFIER = auto()
    INTEGER_CONSTANT = auto()
    FLOAT_CONSTANT = auto()
    STRING_CONSTANT = auto()
    CHAR_CONSTANT = auto()
    TRUE_CONSTANT = auto()

    KW_INT = auto()
    KW_STRING = auto()
    KW_FLOAT = auto()
    KW_CHAR = auto()
    KW_BOOL = auto()

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
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_LET = auto()
    
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
    LPAREN = auto()
    RPAREN = auto()
    SEMICOLON = auto()
    COLON = auto()
    DOT = auto()
    COMMA = auto()
    HASH = auto()
    INVALID = auto()


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
        self.linenum = 1
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

        def make(kind, value=""):
            return Token(kind, linenum, column, value)

        def invalid(value):
            return Token(TokenKind.INVALID, linenum, column, value)

        return make, invalid

    # return one token or eof if end of file
    def lex(self):
        while self.ptr < len(self.input):
            make, invalid = self.tokener()
            c = self.consume()

            match c:
                case _ if 'a' <= c <= 'z' or 'A' <= c <= 'Z':
                    value = c
                    while not self.done() and self.peek().isalnum():
                        value += self.consume()

                    return make(keyword_or_identifier(value), value)

                case '+':
                    if self.try_eat('='):
                        return make(TokenKind.OP_PLUSEQ, '+=')
                    return make(TokenKind.OP_PLUS, '+')

                case '-':
                    if self.try_eat('='):
                        return make(TokenKind.OP_MINUSEQ, '-=')
                    return make(TokenKind.OP_MINUS, '-')

                case '*':
                    if self.try_eat('='):
                        return make(TokenKind.OP_MULTIPLYEQ, '*=')
                    return make(TokenKind.OP_MULTIPLY, '*')

                case '/':
                    if self.try_eat('='):
                        return make(TokenKind.OP_DIVIDEEQ, '/=')
                    
                    if self.try_eat('/'): # throw away comments
                        while not self.done() and self.peek() != '\n':
                            self.consume()
                        continue
                    return make(TokenKind.OP_DIVIDE, '/')

                case '%':
                    if self.try_eat('='):
                        return make(TokenKind.OP_MODULOEQ, '%=')
                    return make(TokenKind.OP_MODULO, '%')

                case '=':
                    if self.try_eat('='):
                        return make(TokenKind.OP_EQUALEQUAL, '==')
                    return make(TokenKind.EQUAL, '=')

                case '<':
                    if self.try_eat('='):
                        return make(TokenKind.OP_LEQ, '<=')
                    return make(TokenKind.OP_LESS, '<')

                case '>':
                    if self.try_eat('='):
                        return make(TokenKind.OP_GEQ, '>=')
                    return make(TokenKind.OP_GREATER, '>')

                case '!':
                    if self.try_eat('='):
                        return make(TokenKind.OP_NOTEQUAL, '!=')
                    return make(TokenKind.OP_NOT, '!')
                
                case '&':
                    value = c
                    if not self.try_eat('&'):
                        if not self.done():
                            value += self.consume()

                        return invalid(value)
                    
                    return make(TokenKind.OP_ANDAND, '&&')
                
                case '|':
                    value = c
                    if not self.try_eat('|'):
                        if not self.done():
                            value += self.consume()

                        return invalid(value)
                    
                    return make(TokenKind.OP_ANDAND, '||')
                
                case _ if '0' <= c <= '9':
                    value = c
                    while not self.done() and self.peek().isdigit():
                        value += self.consume()

                    if self.try_eat('.'):  # float constant
                        value += '.'
                        while not self.done() and self.peek().isdigit():
                            value += self.consume()
                        return make(TokenKind.FLOAT_CONSTANT, value)
                    else:
                        return make(TokenKind.INTEGER_CONSTANT, value)

                case '"':
                    value = c
                    while not self.done() and self.peek() not in '\n\"' :
                        if self.try_eat('\\'):  # skip escaped character
                            value += '\\'
                            if self.done() or self.peek() == '\n':
                                return invalid(value)
                        value += self.consume()
                        continue

                    if not self.try_eat('\"'): #fail since it was not closed
                        return invalid(value)
                    
                    value += '\"'
                    return make(TokenKind.STRING_CONSTANT, value)
                
                case '\'':
                    value = c
                    if self.try_eat('\\'):
                        value += '\\'
                        if self.done() or self.peek() == '\n':
                            return invalid(value)
                    
                    if not self.done():
                        value += self.consume()

                    if not self.try_eat('\''):
                        return invalid(value)
                    
                    value += '\''
                    return make(TokenKind.CHAR_CONSTANT, value)
                
                case '[':
                    return make(TokenKind.LBRACE, c)
                
                case ']':
                    return make(TokenKind.RBRACE, c)
                
                case '{':
                    return make(TokenKind.LBRACE, c)
                
                case '}':
                    return make(TokenKind.RBRACE, c)
                
                case '(':
                    return make(TokenKind.LPAREN, c)
                
                case ')':
                    return make(TokenKind.RPAREN, c)
                
                case ';':
                    return make(TokenKind.SEMICOLON, c)
                
                case ':':
                    return make(TokenKind.COLON, c)

                case '.':
                    return make(TokenKind.DOT, c)
                
                case ',':
                    return make(TokenKind.COMMA, c)
                
                case '#':
                    return make(TokenKind.HASH, c)
                
                case '\n':
                    self.linenum += 1
                    self.column = 0

                case '\r':
                    pass
                
                case ' ':
                    pass

                case '\t':
                    pass

                case _:
                    return invalid(c)
                
        return Token(TokenKind.EOF, -1, -1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} file")

    with open(sys.argv[1], 'r') as f:
        code = f.read()
    
    items = [["Token Kind", "Token Value", "Line Number", "Column"]]
    l = Lexer(code)

    while not (tok := l.lex()).eof():
        items.append([tok.kind.name, tok.value, tok.linenum, tok.column])

    with open(sys.argv[1] + '.lex', 'w') as f:
        f.write(tabulate(items, headers="firstrow"))

    print(f'Table written to {sys.argv[1]}.lex')
