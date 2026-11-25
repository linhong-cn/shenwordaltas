import { Check, ChevronDown, GraduationCap } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { GRADE_LABELS, GRADE_SHORT, GRADES, type Grade } from "../grades";

/** 年级选择器：在顶栏切换深圳小学 1-6 年级词库。 */
export function GradePicker({ grade, onChange }: { grade: Grade; onChange: (g: Grade) => void }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (e: Event) => {
      if (e instanceof KeyboardEvent ? e.key === "Escape" : !box.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("pointerdown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);
  return (
    <div className="grade-picker" ref={box}>
      <button className="grade-btn" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-label={`当前年级：${GRADE_LABELS[grade]}，点击切换`} title="切换年级">
        <GraduationCap size={16} strokeWidth={2} />
        <span>{GRADE_SHORT[grade]}</span>
        <ChevronDown size={14} className={open ? "is-open" : ""} />
      </button>
      {open && (
        <div className="grade-pop" role="dialog" aria-label="选择年级">
          <p className="eyebrow">选择年级 · 深圳小学英语</p>
          <ul>
            {GRADES.map((g) => (
              <li key={g}>
                <button
                  className={g === grade ? "is-on" : ""}
                  onClick={() => {
                    onChange(g);
                    setOpen(false);
                  }}
                >
                  <span className="grade-num">{g}</span>
                  <span className="grade-name">{GRADE_SHORT[g]}</span>
                  {g === grade && <Check size={16} />}
                </button>
              </li>
            ))}
          </ul>
          <p className="grade-hint">切换年级会加载对应词库，各年级学习进度独立保存。</p>
        </div>
      )}
    </div>
  );
}
