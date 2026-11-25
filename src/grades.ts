/** 深圳小学英语年级配置。默认六年级。 */
export const GRADES = [1, 2, 3, 4, 5, 6] as const;
export type Grade = (typeof GRADES)[number];

export const GRADE_LABELS: Record<Grade, string> = {
  1: "一年级",
  2: "二年级",
  3: "三年级",
  4: "四年级",
  5: "五年级",
  6: "六年级",
};

export const GRADE_SHORT: Record<Grade, string> = {
  1: "一下起步",
  2: "二年级",
  3: "三年级",
  4: "四年级",
  5: "五年级",
  6: "六年级",
};

export const DEFAULT_GRADE: Grade = 6;

export const isGrade = (v: unknown): v is Grade => typeof v === "number" && GRADES.includes(v as Grade);

/** 每个年级词库的 datasetId，用于隔离学习进度。 */
export const gradeDatasetId = (g: Grade) => `grade${g}-atlas`;

/** 词库根目录（相对 BASE_URL）。 */
export const gradeAtlasPath = (g: Grade) => `atlas/g${g}`;
