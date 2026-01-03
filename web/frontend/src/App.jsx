import { useState } from "react";
import "./App.css";

import Editor from "@monaco-editor/react";

function App() {
  const [code, setCode] = useState("// test");

  return (
    <>
      <Editor
        height="90vh"
        width="90vh"
        value={code}
        onChange={(value) => setCode(value ?? "")}
      />
    </>
  );
}

export default App;
