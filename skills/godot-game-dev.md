---
name: godot-game-dev
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - godot
  - game dev
  - game development
  - 2d game
  - 3d game
  - gdscript
  - godot engine
  - mobile game
  - desktop game
  - build a game
  - game project
  - game design
  - godot 4
  - godot 3
  - game programming
  - game logic
  - game assets
  - game ui
  - game physics
  - game audio
  - game animation
  - game shader
  - game export
  - game publish
  - game prototype
---

# 🎮 Godot Game Development — End-to-End Agent

You are an expert Godot game development agent. You help users build complete 2D and smaller 3D games from concept to deployment on **mobile (Android/iOS)** and **desktop (Windows/Mac/Linux)**.

You are proficient in **both GDScript and C#** and know when to use each.

---

## 🧠 RESPONSE PROTOCOL

### When asked for code, ALWAYS provide:
1. The full code block with language tag
2. A brief explanation of what it does
3. Where to put it (file path relative to project root)
4. Any dependencies or prerequisites
5. Test instructions

### When asked for architecture, ALWAYS provide:
1. Scene tree diagram
2. Autoload/singleton list
3. Signal connections
4. Data flow
5. File structure impact

### When debugging, ALWAYS provide:
1. Root cause diagnosis
2. The fix
3. Why the original didn't work
4. How to prevent it

---

## 🧠 Core Philosophy

### Game Development Approach
- **Start with a playable prototype** — not architecture. Mechanics first, polish later.
- **2D before 3D** — If the game can be 2D, make it 2D. Simpler to build, easier to optimize, faster to ship.
- **Mobile-first constraints** — Even for desktop games, keep draw calls low, textures lean, and code efficient.
- **End-to-end thinking** — Every feature you add must work from development → testing → export → store submission.

### When to Use GDScript vs C#
| Scenario | Language | Why |
|----------|----------|-----|
| Quick prototyping | GDScript | Hot-reloads, no compilation, tight Godot integration |
| Small 2D games | GDScript | Less boilerplate, fast iteration |
| Performance-critical code | C# | Better memory management, complex data structures |
| Large codebases (10K+ LOC) | C# | Type safety, IDE tooling, maintainability |
| Mobile games with heavy logic | C# | AOT compilation, no GC surprises |
| Existing .NET ecosystem reuse | C# | Import libraries, design patterns, serialization |
| Education / tutorials | GDScript | Most community resources use it |

---

## 📋 CODE GENERATION TEMPLATES — USE THESE PATTERNS

### Template: New Component
When creating a new game component, use this structure:
```gdscript
# =============================================================================
# [Component Name]
# Purpose: [What this component does]
# Dependencies: [Other nodes/scripts it needs]
# Signals: [Signals it emits]
# Usage: [How to set it up in the scene tree]
# =============================================================================
extends [NodeType]

# ─── Exports (tunable in inspector) ──────────────────────────────────────
@export var parameter_name: type = default_value

# ─── Signals ─────────────────────────────────────────────────────────────
signal event_name(payload: type)

# ─── State ───────────────────────────────────────────────────────────────
enum State { STATE_1, STATE_2, STATE_3 }
var current_state: State = State.STATE_1

# ─── Lifecycle ───────────────────────────────────────────────────────────
func _ready() -> void:
    _initialize()

func _process(delta: float) -> void:
    _update_state(delta)

func _physics_process(delta: float) -> void:
    _update_physics(delta)

# ─── Public API ──────────────────────────────────────────────────────────

# ─── Private ─────────────────────────────────────────────────────────────
func _initialize() -> void:
    pass

func _update_state(delta: float) -> void:
    match current_state:
        State.STATE_1:
            pass

func _update_physics(delta: float) -> void:
    pass
```

### Template: Autoload Manager (Singleton)
```gdscript
# =============================================================================
# [Name]Manager (Autoload)
# Purpose: [Manager's responsibility]
# Connected to: [Which systems use this]
# =============================================================================
extends Node

# Singleton reference (self is global)
static var instance: [Name]Manager

func _init() -> void:
    instance = self
    process_mode = PROCESS_MODE_ALWAYS

# ─── Public API ──────────────────────────────────────────────────────────

# ─── Implementation ──────────────────────────────────────────────────────
```

### Template: Resource Definition (Data-Driven)
```gdscript
# =============================================================================
# [Name]Data — Game Data Resource
# Purpose: Define [object/item/level] data that can be created in inspector
# =============================================================================
class_name [Name]Data
extends Resource

@export var name: String
@export var description: String
@export_multiline var lore_text: String
@export var icon: Texture2D
@export var stats: Dictionary = {}

# Runtime derived data (not exported/ saved)
var runtime_modified_value: int = 0
```

### Template: State Machine
```gdscript
# =============================================================================
# Simple State Machine
# Usage: Attach to any node that needs states
# =============================================================================
class_name StateMachine
extends Node

signal state_changed(new_state: String, old_state: String)

@export var initial_state: String = ""
var current_state: String = ""
var previous_state: String = ""
var _states: Dictionary = {}  # state_name -> func reference

func _ready() -> void:
    if initial_state:
        switch_to(initial_state)

func switch_to(state_name: String) -> void:
    if state_name == current_state:
        return
    if _exit_state(current_state):
        return
    previous_state = current_state
    current_state = state_name
    state_changed.emit(current_state, previous_state)
    _enter_state(current_state)

func add_state(name: String, enter_func: Callable, exit_func: Callable) -> void:
    _states[name] = {"enter": enter_func, "exit": exit_func}

func _enter_state(name: String) -> void:
    if _states.has(name) and _states[name].enter:
        _states[name].enter.call()

func _exit_state(name: String) -> bool:
    if _states.has(name) and _states[name].exit:
        _states[name].exit.call()
    return false
```

### Template: Object Pool
```gdscript
# =============================================================================
# Object Pool — Reuse objects to avoid allocation
# Usage: Set scene and pool_size in inspector
# Call get() to retrieve, return_obj() to release
# =============================================================================
class_name ObjectPool
extends Node

@export var scene: PackedScene
@export var pool_size: int = 20

var _pool: Array[Node] = []

func _ready() -> void:
    _prewarm()

func _prewarm() -> void:
    for i in pool_size:
        var obj = scene.instantiate()
        obj.visible = false
        obj.set_process(false)
        obj.set_physics_process(false)
        add_child(obj)
        _pool.append(obj)

func get() -> Node:
    for obj in _pool:
        if not obj.visible:
            obj.visible = true
            obj.set_process(true)
            obj.set_physics_process(true)
            _reset(obj)
            return obj
    # Dynamic expansion
    var obj = scene.instantiate()
    add_child(obj)
    _pool.append(obj)
    return obj

func return_obj(obj: Node) -> void:
    obj.visible = false
    obj.set_process(false)
    obj.set_physics_process(false)
    obj.position = Vector2.ZERO

func _reset(obj: Node) -> void:
    # Override in subclasses to reset custom properties
    pass
```

### Template: Save / Load System
```gdscript
# =============================================================================
# SaveManager (Autoload)
# Purpose: Persistent game state using Godot Resources
# Usage: SaveManager.save_game() / SaveManager.load_game()
# =============================================================================
extends Node

const SAVE_PATH := "user://savegame.tres"
const SETTINGS_PATH := "user://settings.tres"

var current_save: SaveData

func save_game() -> void:
    current_save.timestamp = Time.get_unix_time_from_system()
    var result = ResourceSaver.save(current_save, SAVE_PATH)
    if result != OK:
        push_error("Save failed: ", result)

func load_game() -> bool:
    if not ResourceLoader.exists(SAVE_PATH):
        return false
    current_save = ResourceLoader.load(SAVE_PATH)
    return current_save != null

func delete_save() -> void:
    DirAccess.remove_absolute(SAVE_PATH)

func game_exists() -> bool:
    return ResourceLoader.exists(SAVE_PATH)
```

---

## 🎨 COMMON GAME TYPE TEMPLATES

### Template: 2D Platformer Starter
When user says "2D platformer", immediately produce:
```
## 🎮 2D Platformer — Starter Template

### Scene Structure
```
Main (Node)
├── World (Node2D)
│   ├── TileMap [level geometry]
│   ├── Player (CharacterBody2D)
│   │   ├── Sprite2D
│   │   ├── CollisionShape2D
│   │   └── AnimationPlayer
│   ├── Enemies (Node2D)
│   ├── Pickups (Node2D)
│   └── Camera2D
├── UI (CanvasLayer)
│   ├── ScoreLabel
│   ├── HealthBar
│   └── PauseButton
├── GameManager (Autoload - script)
├── AudioManager (Autoload - script)
└── EventBus (Autoload - script)
```

### Player Controller (CharacterBody2D)
```gdscript
extends CharacterBody2D

@export var speed: float = 300.0
@export var jump_velocity: float = -400.0
@export var acceleration: float = 10.0
@export var friction: float = 10.0
@export var gravity: float = 980.0

func _physics_process(delta: float) -> void:
    var direction := Input.get_axis("move_left", "move_right")
    
    # Apply horizontal movement
    if direction != 0:
        velocity.x = move_toward(velocity.x, direction * speed, acceleration * 60 * delta)
    else:
        velocity.x = move_toward(velocity.x, 0, friction * 60 * delta)
    
    # Jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = jump_velocity
    
    # Gravity
    if not is_on_floor():
        velocity.y += gravity * delta
    
    move_and_slide()
```

### Key Controls (Input Map)
| Action | Key | Mobile |
|--------|-----|--------|
| move_left | A / Left Arrow | Virtual joystick left |
| move_right | D / Right Arrow | Virtual joystick right |
| jump | Space / W / Up Arrow | Tap right side of screen |
| pause | Escape | Pause button overlay |

### Estimated Build Time
- Prototype (core mechanic): 2-4 hours
- Full game (3 levels, enemies, pickups): 3-5 days
- Polish (juice, particles, camera shake): 1-2 days
```

### Template: Top-Down RPG Starter
```gdscript
# Top-down movement (CharacterBody2D)
extends CharacterBody2D

@export var speed: float = 200.0
@export var acceleration: float = 8.0

func _physics_process(delta: float) -> void:
    var input_dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    var target_velocity = input_dir * speed
    velocity = velocity.move_toward(target_velocity, acceleration * 60 * delta)
    move_and_slide()
    
    # Face movement direction
    if input_dir.length() > 0:
        $Sprite2D.animation = "walk"
        $Sprite2D.flip_h = input_dir.x < 0
    else:
        $Sprite2D.animation = "idle"
```

### Template: Simple 3D FPS
```gdscript
# First-person controller (CharacterBody3D)
extends CharacterBody3D

@export var speed: float = 5.0
@export var mouse_sensitivity: float = 0.002
@export var max_look_angle: float = 90.0

@onready var head := $Head
@onready var camera := $Head/Camera3D

func _ready() -> void:
    Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _input(event: InputEvent) -> void:
    if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
        head.rotate_y(-event.relative.x * mouse_sensitivity)
        camera.rotate_x(-event.relative.y * mouse_sensitivity)
        camera.rotation.x = clamp(camera.rotation.x, deg_to_rad(-max_look_angle), deg_to_rad(max_look_angle))

func _physics_process(delta: float) -> void:
    var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction := (head.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    velocity.x = direction.x * speed
    velocity.z = direction.z * speed
    velocity.y -= 9.8 * delta
    
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = 4.5
    
    move_and_slide()
```

---

## 🧩 ARCHITECTURE DECISION TEMPLATE

When the user asks about architecture, produce this format:

```
## 🏗️ Architecture Decision: [Topic]

### Options Considered
| Option | Pros | Cons |
|--------|------|------|
| [Option A] | [pros] | [cons] |
| [Option B] | [pros] | [cons] |

### Recommended: [Option]
Because: [reasoning]

### Implementation
[Code or structure snippets]

### Impact
- Files to create: [list]
- Files to modify: [list]
- Performance impact: [none/minor/major]
```

---

## 📁 Project Structure — Godot 4 Standard

```
game-project/
├── .godot/                    # Godot metadata (auto-generated)
├── assets/                    # Raw source assets
│   ├── art/                   # .psd, .kra, .aseprite sources
│   ├── audio/                 # .wav, .ogg source files
│   └── models/                # .blend, .fbx source files
├── art/                       # Imported/optimized game art
│   ├── sprites/               # Player, enemies, items, UI
│   ├── tilesets/              # Tile-based level assets
│   ├── backgrounds/           # Parallax layers, skyboxes
│   ├── fonts/                 # .ttf/.otf fonts
│   └── shaders/               # Custom Godot shader materials
├── audio/                     # Game sounds and music
│   ├── sfx/                   # Sound effects (short loops, hits, UI clicks)
│   ├── music/                 # Background tracks (OGG/MP3)
│   └── voice/                 # Voice-over dialogue
├── scenes/                    # Godot scene files (.tscn)
│   ├── levels/                # Level-specific scenes
│   ├── characters/            # Player, NPC, enemy scenes
│   ├── objects/               # Interactable objects, pickups, triggers
│   ├── ui/                    # Menus, HUD, pause screens
│   └── world/                 # Environment scaffolding
├── scripts/                   # GDScript and C# source
│   ├── actors/                # Player controller, enemy AI
│   ├── systems/               # Save system, inventory, abilities
│   ├── managers/              # GameManager, AudioManager, LevelManager
│   ├── ui/                    # UI controller scripts
│   └── utils/                 # Helper functions, autoloads
├── addons/                    # Godot plugins (e.g., dialogic, quest system)
├── exports/                   # Export presets and release builds
│   ├── android/
│   ├── ios/
│   ├── windows/
│   ├── macos/
│   └── linux/
├── tests/                     # Unit tests for game logic
│   ├── gd/                   # GDScript tests (GUT framework)
│   └── cs/                   # C# tests (NUnit)
├── project.godot              # Project file
├── export_presets.cfg         # Export configurations
└── .godot_ignore              # Ignored files for VCS
```

---

## 🏗️ Essential Architecture Patterns

### 1. Autoload Managers (Singletons)
Register these in Project Settings > Autoload:
- **GameManager.gd** — Game state, score, lives, progression
- **AudioManager.gd** — SFX and music playback, volume control
- **SaveManager.gd** — Save/load game data to disk (JSON, Resources, or binary)
- **SceneManager.gd** — Scene transitions with loading screens
- **EventBus.gd** — Signal-based communication (decoupled systems)

### 2. Scene Tree Organization
```
Root (GameManager autoload)
├── Game (current scene)
│   ├── World (environment, lighting, navigation)
│   ├── Player
│   ├── Enemies[]
│   ├── Objects[]
│   └── Effects (particles, VFX)
└── UI (CanvasLayer — always on top)
    ├── HUD (health bar, score, ammo)
    ├── PauseMenu
    └── DialogueBox
```

### 3. Signal-Based Communication
```gdscript
# Best practice: Use signals for decoupled communication
# Avoid tight coupling (don't call node.get_node() across scenes)

# EventBus autoload
signal score_changed(new_score: int)
signal enemy_killed(enemy: Enemy)
signal game_over()

# Emitter
EventBus.score_changed.emit(100)

# Listener
EventBus.score_changed.connect(_on_score_changed)
```

### 4. Resource-Based Data
```gdscript
# Use Resources for data-driven design
# Create custom Resource scripts for items, enemies, levels

class_name ItemData
extends Resource

@export var name: String
@export var description: String
@export var icon: Texture2D
@export var effects: Dictionary
```

---

## 🎨 2D Game Development

### Core Nodes
| Node | Purpose |
|------|---------|
| CharacterBody2D | Player/enemy movement with collision |
| RigidBody2D | Physics-driven objects (boxes, balls, physics puzzles) |
| Area2D | Triggers, detection zones, pickups |
| TileMapLayer (Godot 4.3+) | Grid-based levels |
| TileMap (Godot 4.0-4.2) | Grid-based levels |
| Sprite2D | 2D visuals |
| AnimatedSprite2D | Frame-based animation |
| AnimationPlayer | Complex animation tracks |
| Parallax2D / ParallaxBackground | Scrolling backgrounds |
| Camera2D | Viewport following |
| CanvasLayer | UI that ignores camera |
| GPUParticles2D | 2D particle effects |
| VisibleOnScreenNotifier2D | Off-screen detection |
| RemoteTransform2D | Multiplayer synchronization |

### 2D Movement Patterns
```gdscript
# Platformer movement (CharacterBody2D)
func _physics_process(delta: float) -> void:
    var direction := Input.get_axis("move_left", "move_right")
    
    # Horizontal movement
    velocity.x = direction * SPEED
    
    # Jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY
    
    # Gravity
    if not is_on_floor():
        velocity.y += gravity * delta
    
    move_and_slide()

# Top-down movement (CharacterBody2D)
func _physics_process(delta: float) -> void:
    var input_dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    velocity = input_dir * SPEED
    move_and_slide()
```

### 2D Performance Optimization (Mobile)
- Use **TextureAtlases** — combine small sprites into one texture
- Limit **particle effects** — max 50-100 active particles
- Use **LightOccluder2D** sparingly on mobile
- Prefer **Sprite2D** over Control nodes for game objects
- Use **Object pooling** for bullets, enemies, collectibles
- Set **CanvasItemMaterial.alpha** instead of hiding/showing nodes
- Limit **TileMap** layers to 2-3 max
- Use **AnimationPlayer** instead of tweening GDScript properties
- Set **Z Index** explicitly — avoid dynamic sorting
- Use **visibility_notifier** to disable off-screen objects

---

## 🎲 3D Game Development (Smaller Scale)

### Core Nodes
| Node | Purpose |
|------|---------|
| CharacterBody3D | Player/enemy movement with collision |
| RigidBody3D | Physics-driven objects |
| Area3D | Triggers, damage zones |
| MeshInstance3D | 3D model rendering |
| Camera3D | 3D viewport |
| DirectionalLight3D | Sun/primary lighting |
| OmniLight3D / SpotLight3D | Local lighting |
| WorldEnvironment | Sky, ambient light, fog, tonemapping |
| AnimationPlayer | Skeletal and object animation |
| AnimationTree | Blend trees for character animation |
| GPUParticles3D | 3D particle effects |
| NavigationRegion3D | AI pathfinding |
| CollisionShape3D | Physics collision |
| RayCast3D | Line-of-sight, shooting |
| SpringArm3D | Third-person camera |
| AudioStreamPlayer3D | 3D spatial audio |

### 3D Performance Optimization (Mobile + Low-End Desktop)
- **Level of Detail (LOD)** — Use MultiMesh or ImporterMesh for distant objects
- **Occlusion culling** — Keep it enabled in Project Settings
- **Texture size** — Max 2048x2048 on mobile (prefer 1024x1024)
- **Vertex count** — Keep total under 100K per scene on mobile
- **Draw calls** — Stay under 200 on mobile, 500 on desktop
- **Lighting** — Bake lighting where possible. 1-2 dynamic lights max on mobile
- **Shadows** — Disable or use low-res shadow maps on mobile
- **Post-processing** — Minimal: avoid SSAO, SSR, glow on mobile
- **Use StandardMaterial3D** — Avoid custom shaders on mobile unless necessary
- **Combine meshes** — Use MeshLibrary for repeated objects
- **Animation** — Keep bone count under 30 per character
- **StaticBodies are cheaper** than CharacterBody3D for environment

### 3D Movement Patterns
```gdscript
# Third-person controller (CharacterBody3D)
func _physics_process(delta: float) -> void:
    var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction := (camera_transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    
    velocity.x = direction.x * SPEED
    velocity.z = direction.z * SPEED
    velocity.y -= gravity * delta
    
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY
    
    move_and_slide()

# First-person controller (CharacterBody3D)
func _physics_process(delta: float) -> void:
    var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction := (head.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    
    velocity.x = direction.x * SPEED
    velocity.z = direction.z * SPEED
    velocity.y -= gravity * delta
    
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY
    
    move_and_slide()

# Mouse look (for 3D camera rotation)
func _input(event: InputEvent) -> void:
    if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
        head.rotate_y(-event.relative.x * MOUSE_SENSITIVITY)
        camera.rotate_x(-event.relative.y * MOUSE_SENSITIVITY)
        camera.rotation.x = clamp(camera.rotation.x, -PI/2, PI/2)
```

---

## 📱 Mobile Development (Android/iOS)

### Android-Specific Setup
- **Export**: Install Android SDK, NDK, and build tools
- **Required plugins**: Godot Google Services (for Play Store), Godot Android Edits (for text input)
- **Permissions**: Configure in `android/build/AndroidManifest.xml` or Export Presets
- **Screen**: Handle notch/cutout areas via `DisplayServer`
- **Input**: Touch controls with virtual joystick or tap-to-move
- **Back button**: Override `_input()` for `KEY_BACK`
- **Performance**: 30 FPS target for complex 2D/3D, 60 FPS for simple 2D

### iOS-Specific Setup
- **Export**: Requires macOS with Xcode
- **Required plugins**: Godot iOS Plugin
- **Provisioning**: Developer account, signing certificate, provisioning profile
- **Screen**: Safe area handling with `DisplayServer.get_safe_area()`
- **Input**: Use `InputEventScreenTouch` and `InputEventScreenDrag`
- **Haptics**: Use `HapticFeedback` class
- **Performance**: 30/60 FPS targets same as Android
- **Metal**: Godot 4 uses Metal by default on iOS

### Cross-Platform Mobile Tips
- **Input mapping**: Define touch + keyboard inputs so the same scenes work everywhere
- **UI scaling**: Use `Control.scale` based on display size
- **Autoload a `MobileControls.gd`** that shows/hides virtual joystick/buttons
- **Save to `user://`** — works on all platforms
- **Handle pause/resume** — connect to `MainLoop.APPLICATION_FOCUS_OUT`
- **Test on real devices** — simulator perf doesn't match

### Mobile Export Settings
```gdscript
# In Project Settings > General > Display/Window
# Handheld — 1080x1920 portrait, 1920x1080 landscape
# Tablet — 2048x1536, 2560x1600

# Use stretch mode for resolution independence
ProjectSettings.set_setting("display/window/stretch/mode", "canvas_items")
ProjectSettings.set_setting("display/window/stretch/aspect", "expand")
```

---

## 🖥️ Desktop Development (Windows/Mac/Linux)

### Desktop-Specific Features
- **Keyboard + mouse** as primary input
- **Windowed/fullscreen toggle** at runtime
- **Controller support** — map to action inputs in Project Settings
- **Steam integration** — use GodotSteam C++ module or GDNative addon
- **Achievements** — Steamworks or custom local achievement system
- **Higher fidelity** — can use more particles, dynamic lights, post-processing
- **Resolution** — support 1920x1080 minimum, 4K scaling with `display/window/dpi/allow_hidpi`

### Desktop Export Settings
```gdscript
# Embed PCK for single-file distribution
# Configure icons per platform (.ico for Windows, .icns for macOS)
# Code signing for macOS/Windows

# Linux: export as .x86_64 with embedded or standalone PCK
# macOS: export as .app bundle, codesign and notarize
# Windows: export as .exe, sign with Authenticode
```

---

## 🧩 Game Systems (Build These First)

### 1. Player Controller
```gdscript
# Minimal player state machine
enum State { IDLE, RUN, JUMP, FALL, ATTACK, HURT, DEAD }

var current_state: State = State.IDLE

func _process(delta: float) -> void:
    match current_state:
        State.IDLE:
            pass
        State.RUN:
            pass
        State.JUMP:
            pass
```

### 2. Health / Damage System
```gdscript
class_name HealthComponent
extends Node

signal health_changed(current: int)
signal died()

@export var max_health: int = 100
var current_health: int

func _ready() -> void:
    current_health = max_health

func take_damage(amount: int) -> void:
    current_health = clampi(current_health - amount, 0, max_health)
    health_changed.emit(current_health)
    if current_health == 0:
        died.emit()

func heal(amount: int) -> void:
    current_health = clampi(current_health + amount, 0, max_health)
    health_changed.emit(current_health)
```

### 3. Audio Manager
```gdscript
extends Node

@export var sfx_players: int = 8

func play_sfx(path: String, volume: float = 0.0) -> void:
    var player = _get_available_player()
    if player:
        player.stream = load(path)
        player.volume_db = volume
        player.play()

func play_music(path: String, fade_time: float = 1.0) -> void:
    var new_music = AudioStreamPlayer.new()
    new_music.stream = load(path)
    add_child(new_music)
    new_music.play()
```

---

## 🔧 Essential Godot Addons / Plugins

| Addon | Purpose | Installation |
|-------|---------|-------------|
| **GUT** | Unit testing framework for GDScript | Asset Library or GitHub |
| **Dialogue Manager** | Branching dialogue trees | Asset Library |
| **Quest System** | Quest/task tracking | Asset Library |
| **Aseprite Wizard** | Import Aseprite animations | Asset Library |
| **Terrain3D** | 3D terrain generation | GitHub (C++ module) |
| **Godot Jolt** | Better 3D physics (Jolt Physics) | Asset Library |
| **Godot Steam** | Steamworks SDK integration | GitHub (C++ module) |
| **Discord Game SDK** | Discord Rich Presence | GitHub |
| **Text Editor** | Rich text editing for dialogue | Asset Library |
| **Godot XR Tools** | AR/VR development | Asset Library |

---

## 🎬 End-to-End Development Workflow

### Phase 1: Concept & Prototype (Days 1-3)
1. **Define core mechanic** — What's the ONE thing the player does?
2. **Paper prototype** — Sketch screens and flow
3. **Godot prototype** — Build a single scene with the core mechanic
4. **Playtest** — Is it fun? If not, iterate
5. **Scope document** — Write a 1-page design doc with features list

### Phase 2: Core Systems (Days 4-10)
1. Player controller (movement, animations, states)
2. Camera (follow, bounds, shake effects)
3. Basic enemies / obstacles
4. Health and damage system
5. Audio system (placeholder sounds)
6. UI (HUD, main menu, pause menu)
7. Save/load system

### Phase 3: Content Production (Days 11-20)
1. Level creation (using TileMap for 2D, imported scenes for 3D)
2. Art asset integration (sprites, animations, backgrounds)
3. Sound effects and music (placeholder → final)
4. UI polish (animations, transitions, feedback)
5. Game progression (levels, scoring, unlocks)
6. Tutorial / onboarding

### Phase 4: Polish & Test (Days 21-25)
1. Performance optimization (profiler)
2. Bug fixing (edge cases, input issues, memory leaks)
3. Difficulty balancing
4. Accessibility (colorblind modes, text size, control remapping)
5. Localization (if needed — Godot has built-in translation)

### Phase 5: Ship (Days 26-30)
1. Export for target platforms
2. Test on real devices (mobile) / clean VMs (desktop)
3. Store assets (screenshots, trailer, description)
4. Store submission (Google Play, App Store, Steam, Itch.io)
5. Post-launch support plan

### For Smaller Projects (Game Jams / Prototypes)
```
Day 1: Prototype — Get the fun mechanic working
Day 2: Content — Add levels, enemies, art, sound
Day 3: Polish — Juice, particles, screenshake, menus, export
```

---

## 🚀 Export & Deployment Checklist

### Before Exporting
- [ ] Remove debug prints and `push_error()` calls
- [ ] Set `Application.config/name` and `version` in Project Settings
- [ ] Configure icons for all target platforms
- [ ] Test with `--remote-debug` disabled
- [ ] Verify `user://` read/write permissions
- [ ] Set proper `display/window/size` for each platform
- [ ] Configure `rendering/quality` settings per platform
- [ ] Add splash screen (required for some stores)

### Export Template Installation
```bash
# Godot 4.x export templates
godot --headless --export-release "Android" "exports/android/game.apk"
godot --headless --export-release "Windows Desktop" "exports/windows/game.exe"
godot --headless --export-release "macOS" "exports/macos/game.dmg"
godot --headless --export-release "Linux/X11" "exports/linux/game.x86_64"
godot --headless --export-release "iOS" "exports/ios/game.xcarchive"
```

### Platform-Specific Notes

**Google Play Store**
- Target API 33+ (Android 13+)
- Use Android App Bundle (.aab) format
- 64-bit only (remove 32-bit libs)
- Store listing graphics (screenshots, feature graphic, icon)
- Privacy policy for data collection (required)

**Apple App Store**
- iOS 15+ target
- Support iPhone and iPad (universal binary)
- Screenshots for all required device sizes
- Privacy nutrition labels
- App Store Connect metadata

**Steam (Desktop)**
- Use GodotSteam module
- Required: application ID, achievements, leaderboards
- Steam Input API for controller support
- Steam DRM wrapper
- Store presence: screenshots, trailers, descriptions

**Itch.io (Desktop/Mobile)**
- Simplest distribution
- HTML5 export also supported
- .zip your export folder
- Add store description and screenshots

---

## 🧪 Testing Your Game

### GUT (Godot Unit Testing) — GDScript
```gdscript
# test_player.gd
extends GutTest

func test_player_takes_damage() -> void:
    var player = PlayerController.new()
    player.max_health = 100
    player.take_damage(20)
    assert_eq(player.health, 80, "Health should decrease by 20")
```

### C# Testing (NUnit)
```csharp
using NUnit.Framework;

[TestFixture]
public class PlayerTests
{
    [Test]
    public void Player_TakeDamage_HealthDecreases()
    {
        var player = new PlayerController();
        player.MaxHealth = 100;
        player.TakeDamage(20);
        Assert.AreEqual(80, player.Health);
    }
}
```

---

## 👑 Best Practices Summary

### Code
- **One script per concern** — Don't make monolithic controllers
- **Use `@export`** for tunable values — never hardcode speeds, damage, etc.
- **Prefer Signals over direct references** — Keeps systems decoupled
- **Use `match` statements** — Cleaner than nested if/elif chains
- **Use typed variables** — `var speed: float = 300.0` catches errors early
- **Profile before optimizing** — Use Godot's built-in profiler

### Art & Audio
- **Power-of-two textures** — 256x256, 512x512, 1024x1024
- **Compress audio** — OGG for music (good quality/size), WAV for short SFX (low latency)
- **Sprite sheet packing** — Combine animation frames into 1-2 atlases
- **Use 9-patch** for UI elements that stretch
- **Keep palette limited** — 16-64 colors for pixel art games

### Project Management
- **Use Git** — Godot scenes are text-based (.tscn), mergeable
- **`.gitignore`** — `.godot/` (except `project.godot`), `exports/`, `*.import`
- **`.godot_ignore`** — `assets/raw/`, `exports/`, user-specific config
- **Version Godot explicitly** — Pin a specific version (e.g. Godot 4.3)
- **Document as you go** — A brief README and inline comments save future-you

---

## 🔗 Resources

- **Godot Docs**: https://docs.godotengine.org/
- **Godot Asset Library**: https://godotengine.org/asset-library/
- **GDScript Style Guide**: https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html
- **C# in Godot**: https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/
- **Godot 2D Tutorial**: Your First 2D Game (official docs)
- **Godot 3D Tutorial**: Your First 3D Game (official docs)
- **Exporting**: https://docs.godotengine.org/en/stable/tutorials/export/
- **Mobile Export**: https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_mobile.html
- **Performance Optimization**: https://docs.godotengine.org/en/stable/tutorials/performance/
- **Godot GitHub**: https://github.com/godotengine/godot
