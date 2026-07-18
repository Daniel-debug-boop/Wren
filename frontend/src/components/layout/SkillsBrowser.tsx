import { useEffect, useState } from "react";
import { SkillsApi } from "../../api/skills-service/skills-service.api";

export function SkillsBrowser() {
  const [skills, setSkills] = useState<string[]>([]);
  useEffect(() => {
    SkillsApi.searchSkills(50)
      .then((r) => setSkills(r.items?.map((s) => s.name) ?? []))
      .catch(() =>
        setSkills([
          "github",
          "docker",
          "frontend-design",
          "code-review",
          "tdd",
          "qa",
        ]),
      );
  }, []);

  return (
    <div className="p-2">
      {skills.map((s) => (
        <div
          key={s}
          className="mb-1 rounded-md px-2 py-1.5 text-xs transition"
          style={{
            color: 'var(--text-subtle)',
            cursor: 'default',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--surface-hover)';
            e.currentTarget.style.color = 'var(--text)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--text-subtle)';
          }}
        >
          {s}
        </div>
      ))}
    </div>
  );
}
