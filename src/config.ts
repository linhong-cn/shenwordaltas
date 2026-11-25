/** 应用内所有 GitHub 链接统一指向本项目仓库。上游归属以关于页与 README 中的文字署名保留。 */
export const REPO_URL = "https://github.com/linhong-cn/shenwordaltas";

/**
 * 公益入口（与「支持开发者」的赞赏码完全分开）。
 * 优先填腾讯公益项目或「一起捐」链接；留空时回退读取 public/support/charity-qr.jpg。
 * 善款由腾讯公益平台上具有公开募捐资格的慈善组织直接接收，本应用不代收、不经手，
 * 也不从赞赏金额中按比例抽成。二者都没有配置时，页面显示占位。
 */
export const CHARITY_URL = "";
export const CHARITY_LABEL = "前往腾讯公益项目";
export const CHARITY_DESC =
  "如果你想直接做公益，可以点下面的入口。善款由腾讯公益平台上的持证慈善组织接收并开具捐赠票据，与上面的赞赏互不相关；本应用和作者不代收、不经手任何公益款项。";
