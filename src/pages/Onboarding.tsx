import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { useAtlas } from "../atlas/context";
import { store, useStore } from "../store/store";
import { GRADE_LABELS } from "../grades";

const LEVELS = [
  ["上1", "上册起步", "从第一单元开始"],
  ["上2", "上册进阶", "已经会一些啦"],
  ["上3", "上册冲刺", "上册快学完了"],
  ["下1", "下册起步", "开始下册学习"],
  ["下2", "下册进阶", "下册继续加油"],
  ["下3", "下册冲刺", "准备迎接挑战"],
];

export function Onboarding() {
  const atlas = useAtlas();
  const grade = useStore((s) => s.settings.grade);
  const [level, setLevel] = useState(0);
  const [goal, setGoal] = useState(10);
  const finish = () => store.settings({ onboarded: true, startLevel: Math.max(0, atlas.cefr.indexOf(LEVELS[level][0])), dailyNew: goal });
  return (
    <div className="onboard" role="dialog" aria-modal="true" aria-label="欢迎">
      <div className="onboard-card">
        <img className="onboard-art" src={`${import.meta.env.BASE_URL}brand/hero.webp`} alt="" />
        <div className="onboard-body">
          <p className="eyebrow">欢迎来到深词光 · {GRADE_LABELS[grade]}</p>
          <h1 className="display">
            {atlas.count.toLocaleString()} 颗星，
            <br />
            等你一颗颗点亮。
          </h1>
          <fieldset>
            <legend>你从哪里出发？（选择当前学习阶段）</legend>
            <div className="choice-grid">
              {LEVELS.map(([code, name, desc], i) => (
                <button key={code} className={`choice ${level === i ? "is-on" : ""}`} onClick={() => setLevel(i)} aria-pressed={level === i}>
                  <span className={`chip chip-level lv-${code}`}>{code}</span>
                  <b>{name}</b>
                  <small>{desc}</small>
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>每天点亮几颗新星？</legend>
            <div className="segmented segmented-wide">
              {[5, 10, 15, 20].map((n) => (
                <button key={n} className={goal === n ? "is-on" : ""} onClick={() => setGoal(n)} aria-pressed={goal === n}>
                  {n} 颗{n === 10 ? " · 推荐" : ""}
                </button>
              ))}
            </div>
          </fieldset>
          <button className="btn btn-primary btn-xl" onClick={finish}>
            出发 <ArrowRight size={20} />
          </button>
          <p className="muted">不用注册。进度只留在这台设备上，随时可以在「我的」里修改。</p>
        </div>
      </div>
    </div>
  );
}
