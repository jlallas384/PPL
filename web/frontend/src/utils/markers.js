import { languageName } from "../langconfig";

export function setErrorMarkers(editor, tokens, monaco) {
  const markers = tokens
    .filter(({ kind }) => kind == "INVALID")
    .map((token) => {
      const startColumn = token.column + 1;
      const endColumn = startColumn + token.value.length;
      return {
        message: token.diagnostic,
        startColumn,
        endColumn,
        startLineNumber: token.line,
        endLineNumber: token.line,
        severity: monaco.MarkerSeverity.Error,
      };
    });

  monaco.editor.setModelMarkers(editor.getModel(), languageName, markers);
}
