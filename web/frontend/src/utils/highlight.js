export function highlightToken(editor, token, decorationsRef) {
  const startColumn = token.column + 1;
  const endColumn = startColumn + token.value.length;

  const range = new window.monaco.Range(
    token.line,
    startColumn,
    token.line,
    endColumn
  );

  editor.revealPositionNearTop({
    column: startColumn,
    lineNumber: token.line,
  }, editor.Smooth);
  decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [
    {
      range,
      options: {
        inlineClassName: "token-highlight",
      },
    },
  ]);
}

export function clearHighlight(editor, decorationsRef) {
  decorationsRef.current = editor.deltaDecorations(decorationsRef.current, []);
}
