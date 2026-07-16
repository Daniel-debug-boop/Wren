/* ── SuggestionTextarea — Chat textarea with inline ghost text and Tab-to-accept ── */
import { useRef, useCallback, forwardRef, type KeyboardEvent, type ChangeEvent, type TextareaHTMLAttributes } from "react";

interface SuggestionTextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  suggestion?: string | null;
  onAcceptSuggestion?: () => void;
}

export const SuggestionTextarea = forwardRef<HTMLTextAreaElement, SuggestionTextareaProps>(
  ({ suggestion, onAcceptSuggestion, value, onChange, onKeyDown, className, style, ...props }, ref) => {
    const ghostRef = useRef<HTMLDivElement>(null);

    const handleKeyDown = useCallback(
      (e: KeyboardEvent<HTMLTextAreaElement>) => {
        // Tab-to-accept suggestion
        if (e.key === "Tab" && suggestion && !e.shiftKey) {
          e.preventDefault();
          onAcceptSuggestion?.();
          return;
        }
        onKeyDown?.(e);
      },
      [suggestion, onAcceptSuggestion, onKeyDown],
    );

    const ghostText = suggestion && !props.disabled ? suggestion : null;

    return (
      <div className="relative w-full">
        {/* Ghost text overlay (invisible text mirror for sizing) */}
        <div
          ref={ghostRef}
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 px-4 py-3.5 text-sm leading-relaxed whitespace-pre-wrap break-words select-none"
          style={{
            fontFamily: "inherit",
            fontSize: "inherit",
            lineHeight: "inherit",
            letterSpacing: "inherit",
            color: "transparent",
            visibility: "hidden",
            ...(style as React.CSSProperties),
          }}
        >
          {value}
          {ghostText && (
            <span
              className="pointer-events-none"
              style={{
                color: "transparent",
                borderLeft: "2px solid var(--accent)",
                opacity: 0.4,
              }}
            >
              {ghostText}
            </span>
          )}
        </div>

        {/* Ghost text layer (visible overlay) */}
        {ghostText && (
          <div
            className="pointer-events-none absolute inset-0 px-4 py-3.5 overflow-hidden"
            style={{
              fontFamily: "inherit",
              fontSize: "inherit",
              lineHeight: "inherit",
              letterSpacing: "inherit",
              ...(style as React.CSSProperties),
            }}
          >
            <span className="invisible select-none">{value}</span>
            <span
              className="select-none"
              style={{
                color: "var(--text-quiet)",
                opacity: 0.55,
                borderLeft: "2px solid var(--accent)",
                paddingLeft: "2px",
              }}
            >
              {ghostText}
            </span>
          </div>
        )}

        {/* Actual textarea */}
        <textarea
          ref={ref}
          value={value}
          onChange={onChange}
          onKeyDown={handleKeyDown}
          className={className}
          style={style}
          {...props}
        />

        {/* Suggestion hint */}
        {ghostText && (
          <div
            className="absolute bottom-1 right-2 pointer-events-none flex items-center gap-1 text-[9px] font-medium"
            style={{ color: "var(--text-quiet)", opacity: 0.7 }}
          >
            <kbd
              className="inline-flex h-3.5 items-center rounded px-1 text-[8px] font-medium"
              style={{
                background: "color-mix(in srgb, var(--accent) 10%, transparent)",
                color: "var(--accent)",
                border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
              }}
            >
              Tab
            </kbd>
            <span>accept</span>
          </div>
        )}
      </div>
    );
  },
);

SuggestionTextarea.displayName = "SuggestionTextarea";
