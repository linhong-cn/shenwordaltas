import { Download, ExternalLink, Github, Heart, QrCode } from "lucide-react";
import { useEffect, useState } from "react";
import { CHARITY_DESC, CHARITY_LABEL, CHARITY_URL, REPO_URL } from "../config";

const QR_URL = `${import.meta.env.BASE_URL}support/wechat-reward.jpg`;
const CHARITY_QR_URL = `${import.meta.env.BASE_URL}support/charity-qr.jpg`;

type ImageStatus = "loading" | "ready" | "missing";

function useImageStatus(url: string): ImageStatus {
  const [status, setStatus] = useState<ImageStatus>("loading");
  useEffect(() => {
    const img = new Image();
    img.onload = () => setStatus("ready");
    img.onerror = () => setStatus("missing");
    img.src = url;
    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [url]);
  return status;
}

export function Support() {
  const reward = useImageStatus(QR_URL);
  const charityQr = useImageStatus(CHARITY_QR_URL);

  return (
    <div className="page support">
      <header className="page-head">
        <p className="eyebrow">支持</p>
        <h1 className="display">喜欢深词光，就<span className="support-accent">请我喝杯茶吧</span>。</h1>
        <p className="lede">
          深词光免费、无广告、不收集任何学习数据。如果这些单词卡片帮到了孩子，欢迎用微信扫一扫下面的赞赏码，金额随意。你的支持会用于素材整理和后续更新。
        </p>
      </header>

      <div className="support-grid">
        <section className="panel support-qr">
          <div className="support-qr-title">
            <QrCode size={18} />
            <h3>支持开发者 · 微信赞赏码</h3>
          </div>

          {reward === "ready" ? (
            <>
              <a className="support-qr-image" href={QR_URL} target="_blank" rel="noreferrer" aria-label="查看微信赞赏码大图">
                <img src={QR_URL} alt="微信赞赏码，用微信扫一扫即可赞赏" />
              </a>
              <p className="support-qr-hint">用微信「扫一扫」→ 选择金额 → 完成赞赏</p>
              <a className="btn btn-ghost support-save" href={QR_URL} download="深词光-微信赞赏码.jpg">
                <Download size={16} /> 保存赞赏码图片
              </a>
            </>
          ) : reward === "loading" ? (
            <div className="support-placeholder">
              <span className="spinner" />
              <p>正在加载赞赏码…</p>
            </div>
          ) : (
            <div className="support-placeholder">
              <QrCode size={56} strokeWidth={1.2} />
              <p>赞赏码即将上线，感谢你的耐心。</p>
              <p className="muted">你也可以先给项目点一个 Star，同样是对我的支持。</p>
            </div>
          )}
        </section>

        <section className="panel support-notes">
          <h3 className="eyebrow">几点说明</h3>
          <ul className="feature-list">
            <li>
              <b>完全自愿。</b>赞赏不会解锁任何功能，也不影响学习进度，所有内容始终免费开放。
            </li>
            <li>
              <b>金额随意。</b>微信赞赏码单笔上限 200 元，也可自定义金额；付款由微信官方完成，应用不接触任何支付信息。
            </li>
            <li>
              <b>属于赠与。</b>赞赏不构成商品或服务交易，不提供对等回报，也不开具发票。
            </li>
            <li>
              <b>记录由微信保存。</b>收款明细在微信「赞赏码 → 赞赏记录」中查看；本应用不接触、也不保存任何支付信息。
            </li>
            <li>
              <b>公益入口独立。</b>下面的公益链接与赞赏互不挂钩，本应用不代收善款，也不从赞赏金额中抽成。
            </li>
            <li>
              <b>其他支持方式。</b>在 GitHub 上点 Star、反馈问题或分享给需要的朋友，都同样有帮助。
            </li>
          </ul>
          <a className="btn btn-ghost" href={REPO_URL} target="_blank" rel="noreferrer">
            <Github size={18} /> 去 GitHub 点 Star <ExternalLink size={14} />
          </a>
        </section>
      </div>

      <section className="panel support-charity">
        <div className="support-charity-head">
          <Heart size={18} />
          <h3>也想直接支持公益？</h3>
        </div>
        <p className="muted">{CHARITY_DESC}</p>

        {CHARITY_URL ? (
          <a className="btn btn-primary" href={CHARITY_URL} target="_blank" rel="noreferrer">
            {CHARITY_LABEL} <ExternalLink size={16} />
          </a>
        ) : charityQr === "ready" ? (
          <>
            <a className="support-charity-qr" href={CHARITY_QR_URL} target="_blank" rel="noreferrer" aria-label="查看公益项目二维码大图">
              <img src={CHARITY_QR_URL} alt="腾讯公益项目二维码，用微信扫一扫即可捐赠" />
            </a>
            <p className="support-qr-hint">用微信「扫一扫」→ 在腾讯公益完成捐赠</p>
          </>
        ) : (
          <div className="support-placeholder support-placeholder-sm">
            <QrCode size={44} strokeWidth={1.2} />
            <p>公益项目入口即将上线，感谢你的耐心。</p>
          </div>
        )}
      </section>

      <p className="colophon">
        <Heart size={14} /> 谢谢你让这份词库继续生长。
      </p>
    </div>
  );
}
