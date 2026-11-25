import { ArrowUpRight, Database, Github, Heart } from "lucide-react";
import { useAtlas } from "../atlas/context";
import { REPO_URL } from "../config";
import { useStore } from "../store/store";
import { GRADE_LABELS } from "../grades";

const BASE = import.meta.env.BASE_URL;

export function About() {
  const atlas = useAtlas();
  const grade = useStore((s) => s.settings.grade);
  return (
    <div className="page about">
      <header className="about-hero">
        <img src={`${BASE}brand/og.webp`} alt="" />
        <div>
          <p className="eyebrow">关于深词光</p>
          <h1 className="display">一词一画，快乐背词。</h1>
          <p className="lede">
            深词光把沪教版（深圳用）新版{GRADE_LABELS[grade]}上下册的 {atlas.count.toLocaleString()} 个词条，按单元整理成一本可以听、可以看、可以复习的英语图鉴。每个词条带音标、中文释义、例句、常用搭配和英美发音；学会一个，就在星图上点亮一颗星。顶部可以切换一年级到六年级，各年级进度独立保存。
          </p>
          <p className="lede">它无需注册，进度只存在你的浏览器里，随时可以导出。素材来自开源项目 Word Atlas，按 CC BY 4.0 署名使用。</p>
          <div className="about-actions">
            <a className="btn btn-primary" href="#/atlas">
              <Database size={18} /> 打开词汇图鉴
            </a>
            <a className="btn btn-ghost" href={REPO_URL} target="_blank" rel="noreferrer">
              <Github size={18} /> 查看本项目源码
            </a>
            <a className="btn btn-ghost" href={REPO_URL} target="_blank" rel="noreferrer">
              <ArrowUpRight size={18} /> 素材来源与署名
            </a>
            <a className="btn btn-terra" href="#/support">
              <Heart size={18} /> 打赏支持
            </a>
          </div>
        </div>
      </header>

      <div className="about-grid">
        <section className="panel">
          <h3 className="eyebrow">为什么这样学</h3>
          <ul className="feature-list">
            <li>
              <b>先看见。</b>每个词条配一张和词义相关的插画，先看图，再记词。
            </li>
            <li>
              <b>再听懂。</b>英音、美音、短例句和长例句朗读都可以点开听。
            </li>
            <li>
              <b>刚好在快忘时重逢。</b>FSRS 记忆算法只在你快要遗忘时安排复习。
            </li>
            <li>
              <b>分册分单元。</b>上册 6 个单元、下册 6 个单元，可以按册次和单元筛选。
            </li>
            <li>
              <b>进度只属于你。</b>没有账号，没有服务器，数据存在浏览器里，随时能导出。
            </li>
          </ul>
        </section>

        <section className="panel">
          <h3 className="eyebrow">快捷键</h3>
          <dl className="keys">
            <div>
              <dt>
                <kbd>⌘</kbd>
                <kbd>K</kbd> 或 <kbd>/</kbd>
              </dt>
              <dd>搜索任何词</dd>
            </div>
            <div>
              <dt>
                <kbd>1</kbd>–<kbd>4</kbd>
              </dt>
              <dd>选择答案</dd>
            </div>
            <div>
              <dt>
                <kbd>Enter</kbd>
              </dt>
              <dd>确认 / 继续</dd>
            </div>
            <div>
              <dt>
                <kbd>←</kbd> <kbd>→</kbd>
              </dt>
              <dd>词卡里切换上一个、下一个</dd>
            </div>
            <div>
              <dt>
                <kbd>Esc</kbd>
              </dt>
              <dd>关闭弹窗</dd>
            </div>
          </dl>
        </section>

        <section className="panel">
          <h3 className="eyebrow">内容从哪里来</h3>
          <p className="muted">
            词表按沪教牛津版（深圳用）新版教材整理；插画、音标细化、例句、搭配、词族和发音音频来自开源项目 Word Atlas（Word Atlas contributors，CC BY 4.0）。部分短语用的是词库中同根词的配图和详解，已经在词条详情里注明。教材版本请以学校发放的课本为准。
          </p>
          <p className="muted">这是学习用的整理稿，不是教材官方配套资源，也不代表出版社立场。</p>
        </section>

        <section className="panel">
          <h3 className="eyebrow">给开发者</h3>
          <p className="muted">
            <code>public/atlas/g{'{年级}'}/index.json</code> 是各年级词汇索引，<code>entries/</code> 是分块词条，插画和音频放在 <code>img/</code> 与 <code>audio/</code>。应用使用 React + Vite 构建，所有数据本地静态托管。
          </p>
          <p className="muted">
            <a className="link" href={`${REPO_URL}#readme`} target="_blank" rel="noreferrer">
              阅读本项目 README <ArrowUpRight size={14} />
            </a>
            {" · "}
            <a className="link" href={`${REPO_URL}/blob/main/CONTENT_LICENSE.md`} target="_blank" rel="noreferrer">
              内容许可原文 <ArrowUpRight size={14} />
            </a>
          </p>
        </section>
      </div>
      <p className="colophon">
        <Heart size={14} /> 做给每一个在背单词的小学生。
      </p>
    </div>
  );
}
