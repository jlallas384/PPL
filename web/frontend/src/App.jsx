import { useState } from "react";
import "./App.css";

import Editor from "@monaco-editor/react";
import { languageConf, languageDef, languageName } from "./langconfig";

function App() {
  const [code, setCode] = useState("// test");

  function handleEditorWillMount(monaco) {
    monaco.languages.register({
      id: languageName,
    });
    monaco.languages.setMonarchTokensProvider(languageName, languageDef);
    monaco.languages.setLanguageConfiguration(languageName, languageConf);
  }

  return (
    <div className="container">
      <div className="panel editor">
        <div className="header">
          <span>EDITOR</span>
          <buttom className="run-btn">Run</buttom>
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
          <p>
            asdfafasaaaaaaaaaaaaaaaaaaaaaaa1313123213aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaadasdaaaaaaaaaaaaafsafs
            fas asfdsa <br />
            fasdf asdf asdf asf
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
