import { useState } from "react";
import { MonacoEditor } from "../ide/MonacoEditor";

export function CodeEditor() {
  const [content, setContent] = useState("");

  return (
    <div className="h-1/2 border-t border-white/5 bg-[#0a0e14]">
      <MonacoEditor
        filename="untitled.ts"
        content={content}
        onContentChange={setContent}
      />
    </div>
  );
}
