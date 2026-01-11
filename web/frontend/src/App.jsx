import { useState, useRef } from "react";
import "./App.css";

import Editor, { useMonaco } from "@monaco-editor/react";
import { languageConf, languageDef, languageName } from "./langconfig";
import { highlightToken, clearHighlight } from "./utils/highlight";
import { setErrorMarkers } from "./utils/markers";

function App() {
  const [code, setCode] = useState(`
fn main(): int {
    // Type something here...
    print("Hello World!");
}`);
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);

  const editorRef = useRef(null);
  const decorationsRef = useRef([]);
  const monaco = useMonaco();

  function handleEditorWillMount(monaco) {
    monaco.languages.register({
      id: languageName,
    });
    monaco.languages.setMonarchTokensProvider(languageName, languageDef);
    monaco.languages.setLanguageConfiguration(languageName, languageConf);
  }

  function handleEditorDidMount(editor) {
    editorRef.current = editor;
  }

  async function run() {
    setLoading(true);

    const res = await fetch("/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code }),
    });
    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }
    const data = await res.json();

    const { tokens } = data;

    setErrorMarkers(editorRef.current, tokens, monaco);
    setOutput(tokens);
    setLoading(false);
  }

  async function downloadTable() {
    const res = await fetch("/download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code }),
    });

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "lexical_table.txt";
    document.body.appendChild(a);
    a.click();

    a.remove();
    window.URL.revokeObjectURL(url);
  }

  return (
    <div className="container">
      <div className="panel editor">
        <div className="header">
          <span>EDITOR</span>
          <button className="run-btn" onClick={run}>
            Run
          </button>
        </div>
        <div className="wrapper">
          <Editor
            height="100%"
            width="100%"
            value={code}
            onChange={(value) => setCode(value ?? "")}
            beforeMount={handleEditorWillMount}
            onMount={handleEditorDidMount}
            language={languageName}
            theme="vs-dark"
            options={{
              smoothScrolling: true,
            }}
          />
        </div>
      </div>

      <div className="panel output">
        <div className="header">
          <span>OUTPUT</span>
          {output && (
            <button className="run-btn" onClick={downloadTable}>
              Download
            </button>
          )}
        </div>
        <div className="wrapper">
          {loading ? (
            <p>Loading...</p>
          ) : (
            output && (
              <table className="token-table">
                <thead>
                  <tr>
                    <th>Kind</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {output.map((token, index) => (
                    <tr
                      key={index}
                      onMouseEnter={() =>
                        highlightToken(editorRef.current, token, decorationsRef)
                      }
                      onMouseLeave={clearHighlight(
                        editorRef.current,
                        decorationsRef
                      )}
                    >
                      <td className="kind">{token.kind}</td>
                      <td className="value">{token.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
