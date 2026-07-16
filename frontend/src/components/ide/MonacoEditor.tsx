/* ── MonacoEditor — Full code editor with InlineCompletion ghost text and Tab-to-accept ── */
import { useRef, useCallback, useEffect } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

interface InlineSuggestion {
  insertText: string;
  range?: {
    startLineNumber: number;
    startColumn: number;
    endLineNumber: number;
    endColumn: number;
  };
}

interface MonacoEditorProps {
  filename: string;
  content: string;
  language?: string;
  suggestions?: InlineSuggestion[];
  onContentChange?: (value: string) => void;
  readOnly?: boolean;
}

/* Map file extensions to Monaco language IDs */
function extToLanguage(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() || "txt";
  const map: Record<string, string> = {
    ts: "typescript",
    tsx: "typescript",
    js: "javascript",
    jsx: "javascript",
    py: "python",
    rs: "rust",
    go: "go",
    rb: "ruby",
    java: "java",
    kt: "kotlin",
    swift: "swift",
    cpp: "cpp",
    c: "c",
    h: "c",
    cs: "csharp",
    php: "php",
    html: "html",
    css: "css",
    scss: "scss",
    less: "less",
    json: "json",
    yaml: "yaml",
    yml: "yaml",
    md: "markdown",
    sql: "sql",
    sh: "shell",
    bash: "shell",
    dockerfile: "dockerfile",
    toml: "plaintext",
    xml: "xml",
    vue: "html",
    svelte: "html",
  };
  return map[ext] || "plaintext";
}

export function MonacoEditor({
  filename,
  content,
  language,
  suggestions = [],
  onContentChange,
  readOnly = false,
}: MonacoEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof import("monaco-editor") | null>(null);
  const disposerRef = useRef<{ dispose: () => void } | null>(null);
  const currentSuggestions = useRef(suggestions);
  currentSuggestions.current = suggestions;

  const lang = language || extToLanguage(filename);

  const handleEditorMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    /* Register inline completions provider for all languages */
    const m = monaco as unknown as {
      languages: {
        registerInlineCompletionsProvider: (
          lang: string,
          provider: {
            provideInlineCompletions: (
              model: editor.ITextModel,
              position: { lineNumber: number; column: number },
            ) => { items: Array<{ insertText: string; range: object }> };
            handleRejection?: (c: unknown) => void;
          },
        ) => { dispose: () => void };
        Range: new (...args: number[]) => object;
      };
      KeyCode: { Tab: number };
      Position: new (ln: number, col: number) => { lineNumber: number; column: number };
    };
    const disposer = m.languages.registerInlineCompletionsProvider("*", {
      provideInlineCompletions: (model, position) => {
        const suggestions = currentSuggestions.current;
        if (suggestions.length === 0) return { items: [] };

        return {
          items: suggestions.map((s) => ({
            insertText: s.insertText,
            range: s.range
              ? new monaco.Range(
                  s.range.startLineNumber,
                  s.range.startColumn,
                  s.range.endLineNumber,
                  s.range.endColumn,
                )
              : new monaco.Range(
                  position.lineNumber,
                  position.column,
                  position.lineNumber,
                  position.column,
                ),
          })),
        };
      },
      handleRejection: () => {
        /* suggestion rejected — do nothing */
      },
    });

    disposerRef.current = disposer;

    /* Add keybinding to accept inline suggestion with Tab */
    editor.addAction({
      id: "accept-inline-suggestion",
      label: "Accept Inline Suggestion",
      keybindings: [monaco.KeyCode.Tab],
      run: (ed) => {
        ed.trigger("keyboard", "acceptInlineSuggestion", null);
      },
    });
  }, []);

  /* Clean up disposer on unmount */
  useEffect(() => {
    return () => {
      disposerRef.current?.dispose();
    };
  }, []);

  /* Update content when external content changes */
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || !monacoRef.current) return;
    const current = editor.getValue();
    if (current !== content) {
      editor.setValue(content);
    }
  }, [content]);

  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      {/* Tab bar */}
      <div
        className="flex items-center gap-1 px-2 py-1 text-[11px] shrink-0"
        style={{
          background: "var(--surface)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div
          className="flex items-center gap-1.5 rounded-t px-2.5 py-1"
          style={{
            background: "var(--surface-elevated)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            borderBottom: "none",
          }}
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M3 1.5h6a1.5 1.5 0 011.5 1.5v6A1.5 1.5 0 019 10.5H3A1.5 1.5 0 011.5 9V3A1.5 1.5 0 013 1.5z" />
          </svg>
          <span>{filename || "untitled"}</span>
          <span
            className="text-[9px] px-1 rounded"
            style={{
              background: "color-mix(in srgb, var(--accent) 10%, transparent)",
              color: "var(--accent)",
            }}
          >
            {lang}
          </span>
          {/* Inline Completions indicator */}
          {suggestions.length > 0 && (
            <span
              className="text-[9px] px-1.5 py-0.5 rounded-full font-medium"
              style={{
                background: "color-mix(in srgb, var(--color-gold-400) 15%, transparent)",
                color: "var(--color-gold-400)",
              }}
            >
              Tab ⤶
            </span>
          )}
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <Editor
          key={filename}
          defaultLanguage={lang}
          language={lang}
          defaultValue={content}
          theme="vs-dark"
          onChange={(value) => {
            if (value !== undefined) onContentChange?.(value);
          }}
          onMount={handleEditorMount}
          options={{
            readOnly,
            fontSize: 13,
            fontFamily: "'Geist Mono', 'JetBrains Mono', 'Fira Code', monospace",
            lineNumbers: "on",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on",
            tabSize: 2,
            renderWhitespace: "selection",
            padding: { top: 8 },
            suggestOnTriggerCharacters: true,
            quickSuggestions: true,
            inlineSuggest: { enabled: true },
            "semanticHighlighting.enabled": true,
            smoothScrolling: true,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
            formatOnPaste: true,
            autoClosingBrackets: "always",
            autoClosingQuotes: "always",
            autoIndent: "full",
            guides: {
              bracketPairs: true,
              indentation: true,
            },
          }}
        />
      </div>

      {/* Status bar */}
      <div
        className="flex items-center justify-between px-3 py-1 text-[10px] shrink-0"
        style={{
          borderTop: "1px solid var(--border)",
          color: "var(--text-quiet)",
          background: "var(--surface)",
        }}
      >
        <span>
          {filename} · {lang.toUpperCase()}
        </span>
        <span className="flex items-center gap-2">
          {suggestions.length > 0 && (
            <span className="flex items-center gap-1">
              <kbd
                className="inline-flex h-4 items-center rounded px-1 text-[9px] font-medium"
                style={{
                  background: "color-mix(in srgb, var(--accent) 10%, transparent)",
                  color: "var(--accent)",
                  border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
                }}
              >
                Tab
              </kbd>
              <span>accept suggestion</span>
            </span>
          )}
          <span>Monaco</span>
        </span>
      </div>
    </div>
  );
}
