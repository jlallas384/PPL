from enum import Enum
from dataclasses import dataclass

class TokenKind(Enum):
    EOF = -1
    IDENTIFIER = 0
    KW_FN = 1
    KW_IF = 2
    KW_ELSE = 3

@dataclass
class Token:
    kind: TokenKind
    value: str = ""

    def eof(self):
        return self.kind == TokenKind.EOF
    
keywords = {
    kw[3:].lower(): getattr(TokenKind, kw) for kw in dir(TokenKind) if kw.startswith("KW_")
}

def keyword_or_identifier(s):
    return keywords.get(s, TokenKind.IDENTIFIER)

class Lexer:
    def __init__(self, input):
        self.input = input
        self.ptr = 0

    def done(self):
        return self.ptr >= len(self.input)
    
    # return one token or eof if end of file
    def lex(self):
        while self.ptr < len(self.input):
            c = self.input[self.ptr]
            self.ptr += 1

            match c:
                case _ if 'a' <= c <= 'z' or 'A' <= c <= 'Z':
                    value = c
                    while not self.done() and self.input[self.ptr].isalnum():
                        value += self.input[self.ptr]
                        self.ptr += 1
                    return Token(keyword_or_identifier(value), value)
                case ' ':
                    pass

        return Token(TokenKind.EOF)

if __name__ == "__main__":
    s = """
    fn fn fn fn
    if 
    else
    """

    l = Lexer(s)

    while not (tok := l.lex()).eof():
        print(tok)