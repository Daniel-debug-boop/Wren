import { useState } from "react";
import { MonacoEditor } from "../ide/MonacoEditor";

export function CodeEditor() {
  const [content, setContent] = useState("");

  return (
    <div className="h-1/2 border-t" style={{ borderColor: 'var(--border)', background: 'var(--bg)' }}>
      <MonacoEditor
        filename="untitled.ts"
        content={content}
        onContentChange={setContent}
      />
    </div>
  );
}
