import { ChevronLeft, ChevronRight, Download, Images, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { loadOpenAtlas } from "../atlas/data";
import type { Atlas, Entry } from "../atlas/types";
import { GRADE_LABELS, GRADES, gradeAtlasPath, type Grade } from "../grades";
import { go, type Route } from "../lib/router";
import { useStore } from "../store/store";
import { renderWordCard } from "../ui/share";
import { toast } from "../ui/Toast";

type RouteBooks = Extract<Route, { page: "books" }>;
type Part = "上" | "下";

/** g6 ids are `a_u1_*` / `b_u1_*`; g1-5 are `gN_b1_u1_*` / `gN_b2_u1_*`. */
function locate(g: Grade, id: string): { part: Part; unit: number } {
  const m = g === 6 ? id.match(/^([ab])_u(\d+)_/) : id.match(new RegExp(`^g${g}_b([12])_u(\\d+)_`));
  const part: Part = m && (g === 6 ? m[1] === "b" : m[1] === "2") ? "下" : "上";
  return { part, unit: m ? Number(m[2]) : 1 };
}

const PARTS: Part[] = ["上", "下"];

export function BooksPage({ route }: { route: RouteBooks }) {
  const learnGrade = useStore((s) => s.settings.grade);
  const grade: Grade = GRADES.includes(route.grade as Grade) ? (route.grade as Grade) : learnGrade;
  const part: Part = route.part === "下" ? "下" : "上";
  const unit = typeof route.unit === "number" ? route.unit : 1;
  const index = typeof route.index === "number" ? route.index : 0;

  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    setAtlas(null);
    setError(null);
    loadOpenAtlas(grade).then(
      (a) => live && setAtlas(a),
      (e: Error) => live && setError(e.message),
    );
    return () => {
      live = false;
    };
  }, [grade]);

  const units = useMemo(() => {
    const found = new Set<number>();
    for (const w of atlas?.words ?? []) if (locate(grade, w.id).part === part) found.add(locate(grade, w.id).unit);
    return [...found].sort((a, b) => a - b);
  }, [atlas, grade, part]);

  const words = useMemo(() => (atlas?.words ?? []).filter((w) => { const p = locate(grade, w.id); return p.part === part && p.unit === unit; }), [atlas, grade, part, unit]);
  const activeUnit = units.includes(unit) ? unit : (units[0] ?? 1);
  const pos = Math.min(index, Math.max(words.length - 1, 0));
  const word = words[pos];

  const update = useCallback((next: Partial<RouteBooks>) => go({ page: "books", grade, part, unit: activeUnit, index: pos, ...next }), [grade, part, activeUnit, pos]);
  const switchGrade = (g: Grade) => update({ grade: g, part: "上", unit: 1, index: 0 });
  const switchPart = (p: Part) => update({ part: p, unit: 1, index: 0 });
  const switchUnit = (u: number) => update({ unit: u, index: 0 });

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [entry, setEntry] = useState<Entry | null>(null);
  const [rendering, setRendering] = useState(false);
  useEffect(() => {
    let live = true;
    setEntry(null);
    if (atlas && word) atlas.entry(word.id).then((e) => live && setEntry(e)).catch(() => null);
    return () => {
      live = false;
    };
  }, [atlas, word]);
  useEffect(() => {
    let live = true;
    if (!atlas || !entry) return;
    setRendering(true);
    renderWordCard(atlas, entry, grade)
      .then((c) => {
        if (!live || !canvasRef.current) return;
        const target = canvasRef.current;
        target.width = c.width;
        target.height = c.height;
        target.getContext("2d")?.drawImage(c, 0, 0);
        setRendering(false);
      })
      .catch(() => live && setRendering(false));
    return () => {
      live = false;
    };
  }, [atlas, entry, grade]);

  const move = useCallback((d: number) => {
    const next = pos + d;
    if (next < 0 || next >= words.length) return;
    update({ index: next });
  }, [pos, words.length, update]);

  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") move(-1);
      else if (e.key === "ArrowRight") move(1);
    };
    window.addEventListener("keydown", on);
    return () => window.removeEventListener("keydown", on);
  }, [move]);

  const touchX = useRef<number | null>(null);
  const save = async () => {
    if (!atlas || !word || !canvasRef.current) return;
    try {
      const blob = await new Promise<Blob | null>((r) => canvasRef.current!.toBlob(r, "image/jpeg", 0.93));
      if (!blob) throw new Error("no blob");
      const file = new File([blob], `深词光-${GRADE_LABELS[grade]}-${word.id}.jpg`, { type: "image/jpeg" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: word.word }).catch(() => null);
        return;
      }
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = file.name;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
      toast("卡片已保存", "ok");
    } catch {
      toast("保存失败，请稍后再试", "warn");
    }
  };

  return (
    <section className="books-page">
      <div className="books-head">
        <div className="books-title">
          <Images size={22} />
          <div>
            <h1>绘本相册</h1>
            <p>一词一画，按年级与单元翻看</p>
          </div>
        </div>
        <div className="books-filters">
          <div className="books-row">
            <span className="books-label">年级</span>
            <div className="books-chips">
              {GRADES.map((g) => (
                <button key={g} className={g === grade ? "is-on" : ""} onClick={() => switchGrade(g)}>{GRADE_LABELS[g]}</button>
              ))}
            </div>
          </div>
          <div className="books-row">
            <span className="books-label">册别</span>
            <div className="books-chips">
              {PARTS.map((p) => (
                <button key={p} className={p === part ? "is-on" : ""} onClick={() => switchPart(p)}>{GRADE_LABELS[grade]}{p}册</button>
              ))}
            </div>
          </div>
          <div className="books-row">
            <span className="books-label">单元</span>
            <div className="books-chips">
              {units.map((u) => (
                <button key={u} className={u === activeUnit ? "is-on" : ""} onClick={() => switchUnit(u)}>Unit {u}</button>
              ))}
              {!units.length && <span className="books-muted">加载中…</span>}
            </div>
          </div>
        </div>
      </div>

      {error ? (
        <p className="books-muted">{error}</p>
      ) : !word ? (
        <p className="books-muted">暂无词条</p>
      ) : (
        <>
          <div className="books-stage">
            <button className="books-nav" onClick={() => move(-1)} disabled={pos === 0} aria-label="上一张"><ChevronLeft size={28} /></button>
            <div className="books-card" onTouchStart={(e) => (touchX.current = e.touches[0].clientX)} onTouchEnd={(e) => {
              if (touchX.current === null) return;
              const dx = e.changedTouches[0].clientX - touchX.current;
              if (Math.abs(dx) > 48) move(dx > 0 ? -1 : 1);
              touchX.current = null;
            }}>
              {rendering && <span className="spinner" />}
              <canvas ref={canvasRef} className={rendering ? "is-loading" : ""} aria-label={`${word.word} 卡片`} />
            </div>
            <button className="books-nav" onClick={() => move(1)} disabled={pos >= words.length - 1} aria-label="下一张"><ChevronRight size={28} /></button>
          </div>
          <div className="books-bottom">
            <span>{pos + 1} / {words.length} · {GRADE_LABELS[grade]}{part}册 Unit {activeUnit}</span>
            <span className="books-word">{word.word}</span>
            <div className="books-actions">
              <button className="btn" onClick={save}><Download size={16} /> 保存卡片</button>
              <button className="btn" onClick={() => update({ index: 0 })}><X size={16} /> 回到开头</button>
            </div>
          </div>
          <div className="books-strip">
            {words.map((w, i) => (
              <button key={w.id} className={i === pos ? "is-on" : ""} onClick={() => update({ index: i })} title={w.word}>
                <span>{i + 1}</span>
              </button>
            ))}
          </div>
          <p className="books-note">卡片按词库插画实时绘制，右下角标注来源；数据目录 {gradeAtlasPath(grade)}</p>
        </>
      )}
    </section>
  );
}

