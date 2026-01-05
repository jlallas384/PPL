import { useState } from "react";
import "./App.css";

import Editor from "@monaco-editor/react";
import { languageConf, languageDef, languageName } from "./langconfig";

function App() {
  const [code, setCode] = useState("// Type something here..");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleEditorWillMount(monaco) {
    monaco.languages.register({
      id: languageName,
    });
    monaco.languages.setMonarchTokensProvider(languageName, languageDef);
    monaco.languages.setLanguageConfiguration(languageName, languageConf);
  }

  async function run() {
    setLoading(true);

    const res = await fetch("http://localhost:8000/run", {
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

    setOutput(tokens);
    setLoading(false);
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
            language={languageName}
            theme="vs-dark"
          />
        </div>
      </div>

      <div className="panel output">
        <div className="header">
          <span>OUTPUT</span>
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
                    <tr key={index}>
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
