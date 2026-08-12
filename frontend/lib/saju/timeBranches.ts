/**
 * 13지지(야자시/조자시 분리) 매핑 테이블 + 생년월일 select용 범위 상수.
 * - 자시 분리 근거: calculator.py 상단 주석("자시 경계 야자시 처리 검증됨")과
 *   sajupy 반환값의 zi_time_type 필드 — 야자시(23시대)/조자시(0시대)가
 *   실제로 다른 일주를 낼 수 있어 UI에서도 반드시 구분해야 함.
 * - hour 값은 각 시진의 "시작 시각"을 대표값으로 사용, 백엔드(get_saju)에
 *   그대로 전달됨.
 */

export type JijiOption = {
  value: string;
  labelKorean: string;
  labelHanja: string;
  range: string;
  hour: number;
};

// 24시간 순서(00:00~24:00) 그대로 배열해서, 화면 select에서도 위→아래로 하루 흐름과
// 일치하게 보이도록 구성. 야자시(23:00~00:00)는 하루의 "마지막 2시간"이라
// 조자시부터 해시까지 다 나열한 뒤 맨 마지막에 배치.
export const JIJI_OPTIONS: JijiOption[] = [
  { value: "조자시", labelKorean: "조자시", labelHanja: "子時", range: "00:00~01:00", hour: 0 },
  { value: "축시", labelKorean: "축시", labelHanja: "丑時", range: "01:00~03:00", hour: 1 },
  { value: "인시", labelKorean: "인시", labelHanja: "寅時", range: "03:00~05:00", hour: 3 },
  { value: "묘시", labelKorean: "묘시", labelHanja: "卯時", range: "05:00~07:00", hour: 5 },
  { value: "진시", labelKorean: "진시", labelHanja: "辰時", range: "07:00~09:00", hour: 7 },
  { value: "사시", labelKorean: "사시", labelHanja: "巳時", range: "09:00~11:00", hour: 9 },
  { value: "오시", labelKorean: "오시", labelHanja: "午時", range: "11:00~13:00", hour: 11 },
  { value: "미시", labelKorean: "미시", labelHanja: "未時", range: "13:00~15:00", hour: 13 },
  { value: "신시", labelKorean: "신시", labelHanja: "申時", range: "15:00~17:00", hour: 15 },
  { value: "유시", labelKorean: "유시", labelHanja: "酉時", range: "17:00~19:00", hour: 17 },
  { value: "술시", labelKorean: "술시", labelHanja: "戌時", range: "19:00~21:00", hour: 19 },
  { value: "해시", labelKorean: "해시", labelHanja: "亥時", range: "21:00~23:00", hour: 21 },
  { value: "야자시", labelKorean: "야자시", labelHanja: "子時", range: "23:00~00:00", hour: 23 },
];

/** select에서 "시간 모름"을 고르면 이 값이 들어감 — hour: null로 변환하는 기준 */
export const TIME_UNKNOWN_VALUE = "모름";

/** 선택된 시진 value를 백엔드로 보낼 hour(숫자) 또는 null(모름)로 변환 */
export function getHourFromBranch(value: string): number | null {
  if (!value || value === TIME_UNKNOWN_VALUE) return null;
  const found = JIJI_OPTIONS.find((o) => o.value === value);
  return found ? found.hour : null;
}

/**
 * 오늘 날짜를 기준으로 삼기 위한 헬퍼.
 * ※ 사용자의 로컬 시스템 시각 기준 (서버가 아닌 브라우저에서 계산됨).
 */
export function getTodayParts(): { year: number; month: number; day: number } {
  const now = new Date();
  return { year: now.getFullYear(), month: now.getMonth() + 1, day: now.getDate() };
}

const TODAY = getTodayParts();

export const DATE_RANGE = {
  // year.max를 오늘 연도로 자동 계산 — 매년 손으로 고칠 필요 없음
  year: { min: 1900, max: TODAY.year, label: "년도", maxLength: 4 },
  month: { min: 1, max: 12, label: "월", maxLength: 2 },
  day: { min: 1, max: 31, label: "일", maxLength: 2 },
} as const;

export const YEAR_OPTIONS = Array.from(
  { length: DATE_RANGE.year.max - DATE_RANGE.year.min + 1 },
  (_, i) => DATE_RANGE.year.max - i
);

/**
 * 주어진 년/월의 실제 일수를 계산 (윤년 2월 포함).
 * year 또는 month가 비어있으면(아직 선택 전) 31일까지 넉넉하게 반환 —
 * 이후 년/월이 채워지면 자동으로 좁혀짐.
 * new Date(year, month, 0)은 "month월의 마지막 날"을 반환하는 JS 표준 트릭
 * (month는 0-indexed이므로, 다음 달의 0번째 날 = 이번 달의 마지막 날).
 */
export function getDaysInMonth(year: string, month: string): number {
  if (!year || !month) return 31;
  return new Date(Number(year), Number(month), 0).getDate();
}

/**
 * 서버에서 내려온 hour(숫자 또는 null)를 select에 쓸 시진 value로 역변환.
 * hour가 null이면 "시간 모름"(TIME_UNKNOWN_VALUE) 반환.
 * getHourFromBranch()의 역함수 — manage 화면에서 기존 등록 정보를 불러올 때 사용.
 */
export function getBranchFromHour(hour: number | null): string {
  if (hour === null) return TIME_UNKNOWN_VALUE;
  const found = JIJI_OPTIONS.find((o) => o.hour === hour);
  return found ? found.value : "";
}