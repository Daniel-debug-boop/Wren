import { MonacoEditor } from "../ide/MonacoEditor";

export function CodeEditor() {
  return (
    <div className="h-1/2 border-t border-white/5 bg-[#0a0e14]">
      <MonacoEditor />
    </div>
  );
}
