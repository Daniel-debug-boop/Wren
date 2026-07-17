import { useCallback, useRef } from "react";

interface Options {
  axis: "x" | "y";
  min: number;
  max: number;
  value: number;
  onChange: (v: number) => void;
}

export function useResizable({ axis, min, max, value, onChange }: Options) {
  const startRef = useRef(0);
  const startValRef = useRef(0);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      startRef.current = axis === "x" ? e.clientX : e.clientY;
      startValRef.current = value;
      const move = (ev: PointerEvent) => {
        const cur = axis === "x" ? ev.clientX : ev.clientY;
        const delta = cur - startRef.current;
        const next = Math.max(min, Math.min(max, startValRef.current + delta));
        onChange(next);
      };
      const up = () => {
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", up);
      };
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
    },
    [axis, min, max, value, onChange],
  );

  return { onPointerDown, cursor: axis === "x" ? "col-resize" : "row-resize" };
}
