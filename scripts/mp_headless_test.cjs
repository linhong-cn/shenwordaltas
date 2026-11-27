/* 无头模拟：mock wx + Page，跑通新增页面的关键流程 */
const path = require('path');
const MP = '/Users/hong/WorkBuddy/shenwordaltas-mp-v2';

const storage = {};
let toasts = [];
let routed = [];
global.wx = {
    getStorageSync: (k) => (k in storage ? storage[k] : ''),
    setStorageSync: (k, v) => { storage[k] = JSON.parse(JSON.stringify(v)); },
    showToast: (o) => toasts.push(o.title),
    showLoading: () => {}, hideLoading: () => {},
    setClipboardData: () => {},
    navigateTo: (o) => routed.push(o.url), switchTab: (o) => routed.push(o.url), reLaunch: (o) => routed.push(o.url),
    previewImage: () => {}, downloadFile: () => {}, saveImageToPhotosAlbum: () => {},
    getImageInfo: () => {}, hideTabBar: () => {}, showTabBar: () => {},
    setInnerAudioOption: () => {},
    createInnerAudioContext: () => ({
        play() {}, pause() {}, stop() {}, destroy() {},
        onError() {}, onEnded() {}, onCanplay() {},
        set src(v) {}, get src() { return ''; },
    }),
    getFileSystemManager: () => ({ access: () => {} }),
    canvasToTempFilePath: () => {}, saveImageToPhotosAlbum: () => {},
    getWindowInfo: () => ({ pixelRatio: 2 }),
    getSystemInfoSync: () => ({ pixelRatio: 2 }),
    createSelectorQuery: () => {
        const q = {
            in: () => q,
            select: () => ({
                fields: () => ({
                    exec: (cb) => cb([{ node: fakeCanvas, width: 350, height: 390 }]),
                }),
            }),
        };
        return q;
    },
};

let captured = null;
global.Page = (obj) => { captured = obj; };
global.App = (obj) => { captured = obj; };

function load(pageDir, name) {
    captured = null;
    const p = path.join(MP, 'pages', pageDir, name + '.js');
    delete require.cache[require.resolve(p)];
    require(p);
    return captured;
}

function loadApp() {
    captured = null;
    const p = path.join(MP, 'app.js');
    delete require.cache[require.resolve(p)];
    require(p);
    return captured;
}

function instance(cfg) {
    const page = Object.create(cfg);
    page.data = JSON.parse(JSON.stringify(cfg.data || {}));
    page.setData = function (patch, cb) {
        Object.assign(this.data, patch);
        if (cb) cb.call(this);
    };
    return page;
}

// 让 260ms 的翻页定时器同步执行，便于断言
const realSetTimeout = global.setTimeout;
global.setTimeout = (fn) => { fn(); return 0; };

const ctxStub = new Proxy({}, {
    get(t, k) {
        if (k === 'createRadialGradient') return () => ({ addColorStop() {} });
        if (k === 'fillStyle') return t._fs;
        return () => {};
    },
    set(t, k, v) { t[k] = v; return true; },
});
const fakeCanvas = {
    width: 0,
    height: 0,
    getContext: () => ctxStub,
    // 无头环境不跑动画：rAF 只登记不回调，星图绘制一帧即可断言
    requestAnimationFrame: () => 0,
    cancelAnimationFrame: () => {},
};

const results = [];
function check(name, cond, extra) {
    results.push([cond ? 'PASS' : 'FAIL', name, extra === undefined ? '' : String(extra)]);
}

/* ---------- 1. typing 工具 ---------- */
const typing = require(path.join(MP, 'utils/typing.js'));
check('clean 把弯引号归一', typing.clean('don’t') === "don't", typing.clean('don’t'));
check('clean 保留原文空白（与 PWA 一致）', typing.clean('a\tb') === 'a b', JSON.stringify(typing.clean('a\tb')));
check('same 忽略大小写', typing.same('Hello', 'hello'));
check('correctCharacterCount 按位计分', typing.correctCharacterCount('helo', 'hello') === 3);
const d1 = typing.typingDelta('', 'he', 'hello');
check('typingDelta 新增 2 字符全对', d1.total === 2 && d1.correct === 2, JSON.stringify(d1));
const d2 = typing.typingDelta('he', 'hx', 'hello');
check('typingDelta 替换计错', d2.total === 1 && d2.correct === 0, JSON.stringify(d2));
const m1 = typing.typingMetrics(50, 60, 50, 60000);
check('typingMetrics 一分钟 50 字符 → 10WPM', m1.wpm === 10 && m1.accuracy === 83, JSON.stringify(m1));
const m2 = typing.typingMetrics(0, 0, 0, 500);
check('typingMetrics 不足 1 秒不给速度', m2.wpm === 0);

/* ---------- 2. store 新增能力 ---------- */
const store = require(path.join(MP, 'utils/store.js'));
const s0 = store.getSettings();
check('默认未引导', s0.onboarded === false && s0.startLevel === 0, JSON.stringify(s0));
store.patchSettings({ onboarded: true, startLevel: 3, dailyNew: 15 });
const s1 = store.getSettings();
check('设置可持久化', s1.onboarded === true && s1.startLevel === 3 && s1.dailyNew === 15);

store.markMistake(6, 'g6_x_1');
store.markMistake(6, 'g6_x_2');
store.markMistake(6, 'g6_x_1');
check('错题去重后 2 条', store.getMistakes(6).length === 2, JSON.stringify(store.getMistakes(6).map((x) => x.i)));
store.resolveMistake(6, 'g6_x_1');
check('答对 1 次仍留在错题本', store.getMistakes(6).some((x) => x.i === 'g6_x_1'));
store.resolveMistake(6, 'g6_x_1');
check('连续答对 2 次移出错题本', !store.getMistakes(6).some((x) => x.i === 'g6_x_1'));

store.addTyping({ at: Date.now(), mode: 'word', items: 10, wpm: 22, accuracy: 95 });
store.addTyping({ at: Date.now(), mode: 'sentence', items: 10, wpm: 31, accuracy: 90 });
check('打字记录写入', store.getTyping().length === 2);
check('bestTyping 分模式取最大', store.bestTyping('word') === 22 && store.bestTyping('sentence') === 31);

const dump = store.exportBackup();
store.resetAll();
check('重置清空错题与打字', store.getMistakes(6).length === 0 && store.getTyping().length === 0);
const back = store.importBackup(dump);
check('备份可还原', back.ok && store.getTyping().length === 2, JSON.stringify(back));

/* ---------- 3. session 起始阶段 ---------- */
const session = require(path.join(MP, 'utils/session.js'));
store.patchSettings({ startLevel: 0 });
const allFresh = session.freshWords(6, 5);
store.patchSettings({ startLevel: 5 });
const lateFresh = session.freshWords(6, 5);
check('起始阶段过滤新词', allFresh.length === 5 && lateFresh.length === 5 && lateFresh[0].c >= 5,
    'lv0=' + allFresh[0].c + ' lv5=' + lateFresh[0].c);

/* ---------- 4. 练习页流程 ---------- */
store.resetAll();
store.patchSettings({ onboarded: true, startLevel: 0, dailyNew: 10 });
const practiceCfg = load('practice', 'practice');
const page = instance(practiceCfg);
page.onShow();
check('练习页 pool 来自学习路线', page.data.poolCount > 0, 'pool=' + page.data.poolCount);
check('三种模式齐全', page.data.modes.length === 3);
check('四种词源齐全', page.data.sources.length === 4);

page.onModeTap({ currentTarget: { dataset: { k: 'word' } } });
page.start();
check('开始一轮进入答题', page.data.stage === 'round' && page.data.total > 0, 'total=' + page.data.total);
check('题目有目标词', page.data.target.length > 0, page.data.target);

/* 逐项输入正确答案，走完全程 */
let guard = 0;
while (page.data.stage === 'round' && guard < 30) {
    const target = page.data.target;
    page.data.value = '';
    page.onInput({ detail: { value: target } });
    guard++;
}
check('答完自动结算', page.data.stage === 'done', 'stage=' + page.data.stage + ' rounds=' + guard);
check('结算有 WPM 与准确率', typeof page.data.resultWpm === 'number' && page.data.resultAccuracy === 100,
    page.data.resultWpm + ' / ' + page.data.resultAccuracy);
check('打字记录已落库', store.getTyping().length === 1, store.getTyping().length);

/* 听写模式：目标为整句 */
page.again();
check('再来一轮回到答题', page.data.stage === 'round');
page.exitRound();
check('结束后回到选择页', page.data.stage === 'setup');

/* ---------- 5. 引导页 ---------- */
const onbCfg = load('onboard', 'onboard');
const ob = instance(onbCfg);
ob.onLoad();
check('引导页读到当前年级词数', ob.data.count === 1880 || ob.data.count > 0, ob.data.count);
check('六个阶段', ob.data.levels.length === 6);
ob.onLevelTap({ currentTarget: { dataset: { i: 4 } } });
ob.onGoalTap({ currentTarget: { dataset: { n: 15 } } });
ob.finish();
const afterOnb = store.getSettings();
check('引导写入 startLevel/dailyNew', afterOnb.startLevel === 4 && afterOnb.dailyNew === 15, JSON.stringify(afterOnb));

/* ---------- 6. 关于页 / 支持页 ---------- */
const aboutCfg = load('about', 'about');
const ab = instance(aboutCfg);
ab.onLoad();
check('关于页拿到词数与配图', ab.data.count > 0 && ab.data.ogImg.indexOf('/brand/og.webp') > 0, ab.data.ogImg.slice(-28));

const spCfg = load('support', 'support');
const sp = instance(spCfg);
sp.onLoad();
check('赞赏码随包本地化', sp.data.rewardUrl === '/assets/wechat-reward.jpg', sp.data.rewardUrl);
check('公益码无素材时不发 404 请求', sp.data.charityUrl === '');
sp.onRewardError();
check('赞赏码加载失败会降级', sp.data.rewardUrl === '');

/* ---------- 7. 星图页 ---------- */
store.resetAll();
store.patchSettings({ onboarded: true, grade: 6 });
const gxCfg = load('galaxy', 'galaxy');
const gx = instance(gxCfg);
gx.onLoad();
check('星图按当前年级铺星', gx.stars.length === 368, 'stars=' + gx.stars.length);
check('未学时全部暗淡', gx.data.lit === 0 && gx.data.mastered === 0);
const radii = gx.stars.map((s) => Math.hypot(s.x, s.z));
check('星星落在旋臂半径区间', radii.every((r) => r >= 0.1 && r <= 1.25),
    'min=' + Math.min(...radii).toFixed(2) + ' max=' + Math.max(...radii).toFixed(2));

// 点亮两个词后重新载入，检查统计
const map6 = {};
require(path.join(MP, 'utils/atlas-data.js'))['6'].words.forEach((w, i) => { if (i < 3) map6[w.i] = w; });
Object.keys(map6).forEach((id, i) => {
    for (let k = 0; k <= (i === 0 ? 3 : 1); k++) store.review(6, id, 2, {});
});
const gx2 = instance(load('galaxy', 'galaxy'));
gx2.onLoad();
check('已学词计入 lit', gx2.data.lit === 3, 'lit=' + gx2.data.lit);
check('记忆盒 ≥3 计入 mastered', gx2.data.mastered >= 1, 'mastered=' + gx2.data.mastered);

gx.onReady();
check('Canvas 完成首帧投影', (gx.screen || []).length === 368, 'screen=' + (gx.screen || []).length);
check('投影坐标均为有限值', gx.screen.every((p) => isFinite(p.sx) && isFinite(p.sy)));
const inside = gx.screen.filter((p) => p.sx >= 0 && p.sx <= 350 && p.sy >= 0 && p.sy <= 390).length;
check('多数星落在画布内', inside > 200, 'inside=' + inside);

// 点中一颗星应跳详情
const target = gx.screen.find((p) => p.sx > 40 && p.sx < 310 && p.sy > 40 && p.sy < 350);
routed = [];
gx.onTouchStart({ touches: [{ clientX: target.sx, clientY: target.sy }] });
gx.onTouchEnd();
check('点星跳转详情页', routed.length === 1 && routed[0].indexOf('/pages/detail/detail?grade=6&id=' + target.id) === 0, routed[0]);

// 拖动应改变视角且不跳转
routed = [];
const yaw0 = gx.yaw;
gx.onTouchStart({ touches: [{ clientX: target.sx, clientY: target.sy }] });
gx.onTouchMove({ touches: [{ clientX: target.sx + 60, clientY: target.sy + 10 }] });
gx.onTouchEnd();
check('拖动旋转视角', Math.abs(gx.yaw - yaw0) > 0.1, 'dyaw=' + (gx.yaw - yaw0).toFixed(2));
check('拖动不误触跳转', routed.length === 0);

/* ---------- 8. 首次启动引导门 ---------- */
storage['shenword_settings'] = { onboarded: false, grade: 6 };
routed = [];
const appCfg = loadApp();
appCfg.onLaunch();
check('未引导时启动跳引导页', routed.length === 1 && routed[0] === '/pages/onboard/onboard', routed[0]);
storage['shenword_settings'] = { onboarded: true, grade: 6 };
routed = [];
appCfg.onLaunch();
check('已引导不再跳转', routed.length === 0);

/* ---------- 9. 本轮改动：阶段联动 / 绘本全屏 / 星图动画 ---------- */
const atCfg = load('atlas', 'atlas');
const at = instance(atCfg);
at.onLoad();
at.onLevelTap({ currentTarget: { dataset: { i: '2' } } });
check('图鉴阶段筛选可选中', at.data.level === 2, 'level=' + at.data.level);
at.onPartTap({ currentTarget: { dataset: { p: '2' } } });
check('切册别时阶段回到全部阶段', at.data.level === -1, 'level=' + at.data.level);
at.onLevelTap({ currentTarget: { dataset: { i: '1' } } });
at.onUnitTap({ currentTarget: { dataset: { u: '1' } } });
check('切单元时阶段回到全部阶段', at.data.level === -1, 'level=' + at.data.level);

const bkCfg = load('books', 'books');
const bk = instance(bkCfg);
bk.onLoad();
check('绘本已移除连续页码条', bk.data.strip === undefined && !!bk.data.current);
bk.openFull();
check('点插画进入全屏', bk.data.fullscreen === true);
const bkBefore = bk.data.index;
bk.fullNext();
check('全屏内可向后翻页', bk.data.index === bkBefore + 1, bkBefore + '→' + bk.data.index);
bk.fullPrev();
bk.closeFull();
check('可退出全屏', bk.data.fullscreen === false);
check('星图具备动画启停能力', typeof gxCfg.startAnimation === 'function' && typeof gxCfg.stopAnimation === 'function');

/* ---------- 汇总 ---------- */
const fail = results.filter((r) => r[0] === 'FAIL');
results.forEach((r) => console.log(r[0], '|', r[1], r[2] ? ' → ' + r[2] : ''));
console.log('\n共', results.length, '项，失败', fail.length, '项');
process.exit(fail.length ? 1 : 0);
