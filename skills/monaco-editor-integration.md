---
name: monaco-editor-integration
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - monaco
  - code editor
  - visual editor
  - edit code visually
  - monaco editor
  - code editing
  - syntax highlight
  - code view
  - source editor
  - vs code editor
  - microsoft editor
---

# 📝 Monaco Editor Integration — Visual Code Editing

Monaco Editor is the code editor that powers **Visual Studio Code** (by Microsoft). This skill integrates Monaco into Wren for visual, syntax-highlighted code editing of GDScript, C#, Python, TypeScript, and Godot scene files.

---

## Why Monaco Editor?

| Feature | Benefit |
|---------|---------|
| **Syntax highlighting** | GDScript, C#, Python, TypeScript, JSON, and 100+ languages |
| **IntelliSense** | Code completion, parameter hints, quick info |
| **Error highlighting** | See errors in real-time as you type |
| **Multi-cursor editing** | Edit multiple lines at once |
| **Find & Replace** | Regex search across files |
| **Git integration** | See diffs, stage changes, commit |
| **Custom themes** | Dark, light, or custom color schemes |

---

## How to Use Monaco in Your Project

### Option 1: Embedded in Wren Frontend (Recommended)

Monaco Editor can be embedded directly in the Wren web UI. This gives you:

```
┌─────────────────────────────────────────────────┐
│  📝 Wren Code Editor (Monaco)                  │
├─────────────────────────────────────────────────┤
│  File Explorer │  Editor Tab                    │
│  ──────────────│────────────────────────────────│
│  scenes/       │ 1  extends CharacterBody2D     │
│  ├─ main.tscn  │ 2  @export var speed = 300     │
│  ├─ level1.tscn│ 3                              │
│  scripts/      │ 4  func _physics_process(d):   │
│  ├─ player.gd  │ 5      var dir = Input...      │
│  ├─ enemy.gd   │ 6      velocity.x = dir *...   │
│  art/          │ 7      move_and_slide()         │
│  exports/      │ 8                              │
│                │  [Line: 5, Col: 20] [Spaces: 4]│
│  [NEW FILE]    │────────────────────────────────│
│                │  Terminal / Output              │
│  SELECTED:     │ $ godot --headless --quit       │
│  player.gd     │ ✅ Project validates OK         │
└─────────────────────────────────────────────────┘
```

**How to Add to Wren Frontend** (for developers):
```bash
# Install Monaco Editor
cd frontend
npm install @monaco-editor/react monaco-editor
```

### Option 2: Embed in Wren Chat

For non-coders, Monaco can be loaded inside the Wren chat interface whenever you need to review or edit code:

```typescript
import Editor from '@monaco-editor/react';

function CodeReview({ code, language, onEdit }) {
  return (
    <div style={{ height: '400px', border: '1px solid #333', borderRadius: '8px' }}>
      <Editor
        height="100%"
        defaultLanguage={language || 'gdscript'}
        defaultValue={code}
        theme="vs-dark"
        onChange={(value) => onEdit(value)}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          readOnly: false,
          scrollBeyondLastLine: false,
        }}
      />
    </div>
  );
}
```

### Option 3: Monaco for GDScript (Custom Language)

Monaco doesn't have built-in GDScript support, but we can add it:

```typescript
// Register GDScript language in Monaco
monaco.languages.register({ id: 'gdscript' });

// Define GDScript syntax highlighting
monaco.languages.setMonarchTokensProvider('gdscript', {
  keywords: [
    'extends', 'class_name', 'func', 'var', 'const', 'enum', 'signal',
    'if', 'elif', 'else', 'for', 'while', 'match', 'break', 'continue',
    'return', 'self', 'super', 'as', 'is', 'in', 'not', 'and', 'or',
    'true', 'false', 'null', 'void', 'int', 'float', 'bool', 'String',
    'Vector2', 'Vector3', 'Color', 'Node', 'Resource', 'Array', 'Dictionary',
    'static', 'onready', 'export', 'tool', 'yield', 'await',
    'pass', 'assert', 'preload', 'load', 'new', 'instance',
  ],
  // Full tokenizer would cover strings, comments, numbers, etc.
});
```

---

## GDScript Code Editing in Monaco

Monaco provides:
- ✅ Keyword highlighting (extends, func, var, etc.)
- ✅ String/comment coloring
- ✅ Bracket matching
- ✅ Auto-closing brackets and quotes
- ✅ Indentation guides
- ✅ Code folding
- ✅ Multiple cursors (Alt+Click)

**For Godot scene files (.tscn)**: Monaco treats them as plain text or JSON with basic syntax support.

---

## Workflow: Visual Editing + Monaco

```
1. Wren writes code ──► 2. You see it in Monaco ──► 3. Review/edit visually
       │                                                  │
       ▼                                                  ▼
4. Save changes ──► 5. Wren validates ──► 6. Test ──► 7. Export
```

**For non-coders**: Monaco shows you the code visually, but you don't need to edit it. You can just read it and describe changes in plain English. Wren handles the actual code editing.

**For developers**: Monaco gives you full VS Code-quality editing with syntax highlighting, IntelliSense, and real-time error checking. Edit GDScript, C#, Python, or TypeScript directly.

---

## Monaco in Wren Chat — UI Concept

When the agent shows you code, it renders as a Monaco editor block:

```
┌──────────────────────────────────────────────────┐
│  📄 player.gd — Player Controller                │
│  ┌──────────────────────────────────────────────┐│
│  │  1  extends CharacterBody2D                  ││
│  │  2                                           ││
│  │  3  @export var speed: float = 300.0         ││
│  │  4  @export var jump_velocity: float = -400  ││
│  │  5                                           ││
│  │  6  func _physics_process(delta: float):      ││
│  │  7      var direction = Input.get_axis(...)  ││
│  │  8      velocity.x = direction * speed       ││
│  │  9      move_and_slide()                     ││
│  └──────────────────────────────────────────────┘│
│  [💾 Save] [🔄 Reset] [▶ Run Test]               │
└──────────────────────────────────────────────────┘
```

This makes code accessible to both:
- **Non-coders**: Can see what the code looks like, point to lines they want changed
- **Coders**: Can edit directly in Monaco and save
