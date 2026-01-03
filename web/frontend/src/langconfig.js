export const languageName = "unk";

//https://github.com/microsoft/monaco-editor/blob/main/src/basic-languages/rust/rust.ts
export const languageDef = {
  defaultToken: "invalid",
  keywords: ["if", "fn", "else", "class"],

  operators: [
    "!",
    "!=",
    "%",
    "%=",
    "&",
    "&=",
    "&&",
    "*",
    "*=",
    "+",
    "+=",
    "-",
    "-=",
    "->",
    ".",
    "..",
    "...",
    "/",
    "/=",
    ":",
    ";",
    "<<",
    "<<=",
    "<",
    "<=",
    "=",
    "==",
    "=>",
    ">",
    ">=",
    ">>",
    ">>=",
    "@",
    "^",
    "^=",
    "|",
    "|=",
    "||",
    "_",
    "?",
    "#",
  ],

  escapes: /\\([nrt0\"''\\]|x\h{2}|u\{\h{1,6}\})/,
  delimiters: /[,]/,
  symbols: /[\#\!\%\&\*\+\-\.\/\:\;\<\=\>\@\^\|_\?]+/,
  intSuffixes: /[iu](8|16|32|64|128|size)/,
  floatSuffixes: /f(32|64)/,

  tokenizer: {
    root: [
      // Raw string literals
      [
        /r(#*)"/,
        { token: "string.quote", bracket: "@open", next: "@stringraw.$1" },
      ],
      [
        /[a-zA-Z][a-zA-Z0-9_]*!?|_[a-zA-Z0-9_]+/,
        {
          cases: {
            "@keywords": "keyword",
            "@default": "identifier",
          },
        },
      ],
      [/"/, { token: "string.quote", bracket: "@open", next: "@string" }],
      { include: "@numbers" },
      // Whitespace + comments
      { include: "@whitespace" },
      [
        /@delimiters/,
        {
          cases: {
            "@keywords": "keyword",
            "@default": "delimiter",
          },
        },
      ],

      [/[{}()\[\]<>]/, "@brackets"],
      [/@symbols/, { cases: { "@operators": "operator", "@default": "" } }],
    ],

    whitespace: [
      [/[ \t\r\n]+/, "white"],
      [/\/\*/, "comment", "@comment"],
      [/\/\/.*$/, "comment"],
    ],

    comment: [
      [/[^\/*]+/, "comment"],
      [/\/\*/, "comment", "@push"],
      ["\\*/", "comment", "@pop"],
      [/[\/*]/, "comment"],
    ],

    string: [
      [/[^\\"]+/, "string"],
      [/@escapes/, "string.escape"],
      [/\\./, "string.escape.invalid"],
      [/"/, { token: "string.quote", bracket: "@close", next: "@pop" }],
    ],

    stringraw: [
      [/[^"#]+/, { token: "string" }],
      [
        /"(#*)/,
        {
          cases: {
            "$1==$S2": {
              token: "string.quote",
              bracket: "@close",
              next: "@pop",
            },
            "@default": { token: "string" },
          },
        },
      ],
      [/["#]/, { token: "string" }],
    ],

    numbers: [
      //Octal
      [/(0o[0-7_]+)(@intSuffixes)?/, { token: "number" }],
      //Binary
      [/(0b[0-1_]+)(@intSuffixes)?/, { token: "number" }],
      //Exponent
      [
        /[\d][\d_]*(\.[\d][\d_]*)?[eE][+-][\d_]+(@floatSuffixes)?/,
        { token: "number" },
      ],
      //Float
      [/\b(\d\.?[\d_]*)(@floatSuffixes)?\b/, { token: "number" }],
      //Hexadecimal
      [/(0x[\da-fA-F]+)_?(@intSuffixes)?/, { token: "number" }],
      //Integer
      [/[\d][\d_]*(@intSuffixes?)?/, { token: "number" }],
    ],
  },
};
