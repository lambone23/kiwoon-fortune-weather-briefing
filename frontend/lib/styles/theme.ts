// frontend/lib/styles/theme.ts
// 챕터 2(2-8 결론)에서 확정한 컬러 팔레트. 색상 변경 시 이 파일만 수정하면
// 전 화면에 전파됨 — 절대 컴포넌트 파일에 헥스값을 직접 쓰지 않는다.

export const color = {
  bgPage: "#FAF9F6",
  bgCard: "#FFFFFF",
  bgHighlight: "#F1EDE4", // 총운 강조 박스 등

  textPrimary: "#2B2A27",
  textSecondary: "#8A8578",
  textCaption: "#B5B2A8",

  border: "#E4E1D8",
  borderField: "#DAD7CC",

  point: "#3D4B6E",     // 포인트 컬러 단일. 카드 헤더/버튼/강조 아이콘 전부 이걸로 통일
  pointText: "#C9CFDD", // 포인트 배경 위에 얹는 보조 텍스트(예: 카드 헤더 부제)

  success: "#3B6D11",
  successBg: "#EAF3DE",
  warning: "#854F0B",
  warningBg: "#FAEEDA",
  danger: "#B5615A",
} as const;

export const font = {
  family: "'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif",
  size: {
    caption: "11px",
    small: "12px",
    body: "13px",
    label: "14px",
    title: "17px",
    heading: "19px",
  },
} as const;

export const radius = {
  sm: "8px",
  md: "10px",
  lg: "14px",
  xl: "20px",
} as const;

export const spacing = {
  xs: "6px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "20px",
} as const;