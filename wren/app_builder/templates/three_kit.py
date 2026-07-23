"""Three.js / WebGL 3D Infrastructure Kit — generates complete 3D setup code.

Provides generator functions for:
  - Three.js scene setup with render loop, camera, controls
  - React-Three-Fiber (R3F) component boilerplate
  - WebGL context management with fallback
  - Asset loading pipeline (GLTF, textures)
  - Animation helpers with performance optimization
  - GPU detection and WebGPU fallback
"""

from __future__ import annotations

import json
from typing import Any


def generate_package_json(project_name: str, has_3d: bool = True) -> dict[str, Any]:
    """Generate package.json with 3D dependencies."""
    deps: dict[str, str] = {
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
        "react-router-dom": "^7.0.0",
    }
    dev_deps: dict[str, str] = {
        "@vitejs/plugin-react": "^4.3.0",
        "vite": "^6.0.0",
        "vitest": "^2.0.0",
        "typescript": "^5.5.0",
        "@types/react": "^19.0.0",
        "@types/react-dom": "^19.0.0",
    }

    if has_3d:
        deps.update({
            "three": "^0.170.0",
            "@react-three/fiber": "^8.17.0",
            "@react-three/drei": "^9.114.0",
            "@react-three/postprocessing": "^2.16.0",
            "@react-three/rapier": "^1.5.0",
        })
        dev_deps.update({
            "@types/three": "^0.170.0",
        })

    return {
        "name": project_name.lower().replace(" ", "-"),
        "private": True,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview",
            "test": "vitest run",
        },
        "dependencies": deps,
        "devDependencies": dev_deps,
    }


def generate_tsconfig() -> str:
    """Generate tsconfig.json with strict mode and 3D-friendly settings."""
    return json.dumps({
        "compilerOptions": {
            "target": "ES2022",
            "lib": ["ES2022", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "moduleResolution": "bundler",
            "jsx": "react-jsx",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "allowImportingTsExtensions": True,
        },
        "include": ["src"],
    }, indent=2) + "\n"


def generate_vite_config(has_3d: bool = True) -> str:
    """Generate Vite config with 3D-friendly settings."""
    return """\
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    test: {
        environment: 'jsdom',
        globals: true,
    },
""" + (
        """
    // Optimize 3D/WebGL asset handling
    assetsInclude: ['**/*.glb', '**/*.gltf', '**/*.hdr', '**/*.basis'],
    build: {
        target: 'es2022',
        rollupOptions: {
            output: {
                manualChunks: {
                    three: ['three'],
                    r3f: ['@react-three/fiber', '@react-three/drei'],
                },
            },
        },
    },
"""
        if has_3d
        else ""
    ) + """\
})
"""


def generate_three_scene_tsx() -> str:
    """Generate a complete Three.js scene component with React-Three-Fiber.

    Includes:
    - Canvas with responsive sizing
    - Camera controls (OrbitControls)
    - Lighting setup (ambient + directional)
    - Environment map
    - Performance monitoring (Stats)
    - Resize handling
    - GPU resource cleanup
    """
    return """\
import React, { useRef, useMemo, Suspense } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import {
    OrbitControls,
    Environment,
    Stats,
    PerspectiveCamera,
    ContactShadows,
    useProgress,
    Html,
} from '@react-three/drei'
import * as THREE from 'three'

// ── Loading indicator ───────────────────────────────────────────────

function Loader() {
    const { progress, active } = useProgress()
    if (!active) return null
    return (
        <Html center>
            <div style={{
                color: '#e2e8f0',
                fontFamily: 'monospace',
                fontSize: '14px',
                textAlign: 'center',
            }}>
                <div style={{
                    width: '120px',
                    height: '2px',
                    background: '#1e293b',
                    borderRadius: '2px',
                    overflow: 'hidden',
                    margin: '8px auto',
                }}>
                    <div style={{
                        width: `${progress}%`,
                        height: '100%',
                        background: '#6366f1',
                        transition: 'width 0.3s ease',
                    }} />
                </div>
                <div>{Math.round(progress)}% loaded</div>
            </div>
        </Html>
    )
}

// ── Scene content ────────────────────────────────────────────────────

function SceneContent() {
    const meshRef = useRef<THREE.Mesh>(null!)
    const { viewport } = useThree()

    // Animate
    useFrame((state, delta) => {
        if (meshRef.current) {
            meshRef.current.rotation.x += delta * 0.3
            meshRef.current.rotation.y += delta * 0.5
        }
    })

    return (
        <group>
            {/* Ambient light for base illumination */}
            <ambientLight intensity={0.4} />

            {/* Main directional light with shadows */}
            <directionalLight
                position={[5, 10, 5]}
                intensity={1.5}
                castShadow
                shadow-mapSize-width={2048}
                shadow-mapSize-height={2048}
            />

            {/* Fill light */}
            <directionalLight position={[-5, 0, 5]} intensity={0.5} />

            {/* Rim light */}
            <directionalLight position={[0, -5, -5]} intensity={0.3} />

            {/* Main object - animated torus knot */}
            <mesh ref={meshRef} castShadow receiveShadow>
                <torusKnotGeometry args={[1, 0.3, 128, 16]} />
                <meshPhysicalMaterial
                    color="#6366f1"
                    metalness={0.6}
                    roughness={0.2}
                    envMapIntensity={1.5}
                    clearcoat={0.3}
                    clearcoatRoughness={0.4}
                />
            </mesh>

            {/* Ground plane */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
                <planeGeometry args={[20, 20]} />
                <shadowMaterial transparent opacity={0.4} />
            </mesh>

            {/* Contact shadows */}
            <ContactShadows
                position={[0, -1.9, 0]}
                opacity={0.6}
                scale={10}
                blur={2}
                far={4}
            />

            {/* Camera controls */}
            <OrbitControls
                enableDamping
                dampingFactor={0.05}
                minDistance={2}
                maxDistance={20}
                autoRotate
                autoRotateSpeed={1.0}
            />
        </group>
    )
}

// ── Main Scene component ──────────────────────────────────────────────

interface SceneProps {
    cameraPosition?: [number, number, number]
    controls?: boolean
    shadows?: boolean
    className?: string
}

export default function Scene({
    cameraPosition = [0, 0, 5],
    controls = true,
    shadows = true,
    className = '',
}: SceneProps) {
    return (
        <div
            className={className}
            style={{
                width: '100%',
                height: '100%',
                minHeight: '400px',
                position: 'relative',
            }}
        >
            <Canvas
                shadows={shadows}
                dpr={[1, 2]} // Responsive pixel ratio
                gl={{
                    antialias: true,
                    alpha: false,
                    powerPreference: 'high-performance',
                    stencil: false,
                    depth: true,
                }}
                onCreated={({ gl }) => {
                    // Set default clear color
                    gl.setClearColor('#0f0f1a')

                    // Handle context loss
                    gl.domElement.addEventListener('webglcontextlost', (e) => {
                        e.preventDefault()
                        console.warn('WebGL context lost — attempting recovery...')
                        setTimeout(() => gl.forceContextRestore(), 500)
                    })
                }}
            >
                {/* Responsive camera */}
                <PerspectiveCamera
                    makeDefault
                    position={cameraPosition}
                    fov={45}
                    near={0.1}
                    far={100}
                />

                {/* Environment map for reflections */}
                <Suspense fallback={<Loader />}>
                    <Environment
                        preset="city"
                        background={false}
                    />
                    <SceneContent />
                </Suspense>

                {/* Performance stats in development */}
                {import.meta.env.DEV && <Stats />}
            </Canvas>
        </div>
    )
}
"""


def generate_three_helpers_ts() -> str:
    """Generate utility functions for Three.js operations.

    Includes:
    - Object disposal (prevent GPU leaks)
    - Random positioning helpers
    - Animation tweening
    - Raycaster helpers
    - GLTF loader wrapper
    - Responsive sizing
    """
    return """\
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'

// ── GPU Resource Cleanup ────────────────────────────────────────────

/**
 * Dispose of a Three.js object and all its children to prevent GPU memory leaks.
 * Call this when removing objects from the scene.
 */
export function disposeObject(obj: THREE.Object3D): void {
    obj.traverse((child) => {
        if (child instanceof THREE.Mesh) {
            child.geometry?.dispose()
            if (Array.isArray(child.material)) {
                child.material.forEach(disposeMaterial)
            } else {
                disposeMaterial(child.material)
            }
        }
        if (child instanceof THREE.Light) {
            child.dispose()
        }
    })
}

function disposeMaterial(material: THREE.Material): void {
    material.dispose()
    // Dispose textures
    for (const key of Object.keys(material)) {
        const value = (material as any)[key]
        if (value instanceof THREE.Texture) {
            value.dispose()
        }
    }
}

// ── GLTF Model Loader ────────────────────────────────────────────────

const loader = new GLTFLoader()
const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')
loader.setDRACOLoader(dracoLoader)

/**
 * Load a GLTF model with Draco compression support.
 */
export function loadModel(url: string): Promise<THREE.Group> {
    return new Promise((resolve, reject) => {
        loader.load(
            url,
            (gltf) => resolve(gltf.scene),
            undefined,
            (error) => reject(error)
        )
    })
}

// ── Geometry Helpers ─────────────────────────────────────────────────

/**
 * Create a random position within a spherical volume.
 */
export function randomPositionInSphere(radius: number = 5): THREE.Vector3 {
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    const r = radius * Math.cbrt(Math.random())
    return new THREE.Vector3(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi),
    )
}

/**
 * Create a random position on a grid.
 */
export function randomGridPosition(
    count: number,
    spacing: number = 2,
): THREE.Vector3 {
    const gridSize = Math.ceil(Math.sqrt(count))
    const x = (Math.floor(Math.random() * gridSize) - gridSize / 2) * spacing
    const z = (Math.floor(Math.random() * gridSize) - gridSize / 2) * spacing
    return new THREE.Vector3(x, 0, z)
}

// ── Animation Helpers ────────────────────────────────────────────────

/**
 * Linear interpolation between two values.
 */
export function lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t
}

/**
 * Smooth damp (easing) — useful for camera follow.
 */
export function smoothDamp(
    current: number,
    target: number,
    velocity: { value: number },
    smoothTime: number,
    deltaTime: number,
    maxSpeed: number = Infinity,
): number {
    const omega = 2 / smoothTime
    const x = omega * deltaTime
    const exp = 1 / (1 + x + 0.48 * x * x + 0.235 * x * x * x)
    const change = current - target
    const maxChange = maxSpeed * smoothTime
    const clampedChange = Math.min(Math.abs(change), maxChange) * Math.sign(change)
    const tempTarget = current - clampedChange
    const temp = (velocity.value + omega * clampedChange) * deltaTime
    velocity.value = (velocity.value - omega * temp) * exp
    return tempTarget + (clampedChange + temp) * exp
}

// ── Responsive Sizing ────────────────────────────────────────────────

/**
 * Calculate responsive size based on viewport and distance from camera.
 */
export function responsiveSize(
    baseSize: number,
    distance: number,
    fov: number = 45,
    viewportHeight: number = window.innerHeight,
): number {
    const vFov = (fov * Math.PI) / 180
    const heightAtDistance = 2 * Math.tan(vFov / 2) * distance
    const scaleFactor = heightAtDistance / (viewportHeight * 0.01)
    return baseSize * scaleFactor
}

// ── Color Helpers ────────────────────────────────────────────────────

/**
 * Generate a random color from a palette.
 */
export function randomFromPalette(palette: string[]): string {
    return palette[Math.floor(Math.random() * palette.length)]
}

/**
 * Convert hex color to Three.js Color.
 */
export function hexToThreeColor(hex: string): THREE.Color {
    return new THREE.Color(hex)
}

// ── WebGL Support Detection ─────────────────────────────────────────

export interface WebGLSupport {
    supported: boolean
    version: number
    vendor: string
    renderer: string
    maxTextureSize: number
    hasWebGL2: boolean
    hasWebGPU: boolean
}

/**
 * Detect WebGL/WebGPU support and capabilities.
 */
export function detectWebGLSupport(): WebGLSupport {
    const info: WebGLSupport = {
        supported: false,
        version: 0,
        vendor: '',
        renderer: '',
        maxTextureSize: 0,
        hasWebGL2: false,
        hasWebGPU: false,
    }

    try {
        const canvas = document.createElement('canvas')

        // WebGL 1
        const gl1 = canvas.getContext('webgl') as WebGLRenderingContext | null
        if (gl1) {
            info.supported = true
            info.version = 1
            const debugInfo = gl1.getExtension('WEBGL_debug_renderer_info')
            if (debugInfo) {
                info.vendor = gl1.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
                info.renderer = gl1.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
            }
            info.maxTextureSize = gl1.getParameter(gl1.MAX_TEXTURE_SIZE)
        }

        // WebGL 2
        const gl2 = canvas.getContext('webgl2') as WebGL2RenderingContext | null
        if (gl2) {
            info.hasWebGL2 = true
            info.version = 2
        }

        // WebGPU (experimental)
        if ('gpu' in navigator) {
            info.hasWebGPU = true
        }
    } catch {
        // WebGL not available
    }

    return info
}

// ── Frustum Culling Helper ──────────────────────────────────────────

/**
 * Check if a position is within the camera frustum (for culling).
 */
export function isInFrustum(
    position: THREE.Vector3,
    camera: THREE.Camera,
    margin: number = 1.5,
): boolean {
    const frustum = new THREE.Frustum()
    const projScreenMatrix = new THREE.Matrix4()
    projScreenMatrix.multiplyMatrices(
        camera.projectionMatrix,
        camera.matrixWorldInverse,
    )
    frustum.setFromProjectionMatrix(projScreenMatrix)
    return frustum.containsPoint(position)
    }
"""


def generate_shader_glsl() -> str:
    """Generate a GLSL shader example for custom WebGL effects."""
    return """\
// ── Vertex Shader ──────────────────────────────────────────────────

export const vertexShader = `
varying vec2 vUv;
varying vec3 vPosition;
varying vec3 vNormal;

void main() {
    vUv = uv;
    vPosition = position;
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

// ── Fragment Shader ────────────────────────────────────────────────

export const fragmentShader = `
uniform float uTime;
uniform vec3 uColor;
uniform vec3 uGlowColor;

varying vec2 vUv;
varying vec3 vPosition;
varying vec3 vNormal;

void main() {
    // Calculate fresnel effect (edge glow)
    vec3 viewDirection = normalize(cameraPosition - vPosition);
    float fresnel = 1.0 - dot(viewDirection, vNormal);
    fresnel = pow(fresnel, 3.0);

    // Base color with time-based animation
    float pulse = sin(uTime * 0.5 + vUv.x * 3.14) * 0.5 + 0.5;
    vec3 baseColor = mix(uColor, uGlowColor, pulse * 0.3);

    // Add fresnel glow
    vec3 finalColor = mix(baseColor, uGlowColor, fresnel * 0.6);

    gl_FragColor = vec4(finalColor, 1.0);
}
`
"""
