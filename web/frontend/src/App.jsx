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
    <>
      <Editor
        height="90vh"
        width="90vh"
        value={code}
        onChange={(value) => setCode(value ?? "")}
        beforeMount={handleEditorWillMount}
        language={languageName}
        theme="vs-dark"
      />
    </>
  );
}

export default App;
