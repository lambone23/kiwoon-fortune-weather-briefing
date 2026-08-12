// frontend/lib/styles/common.ts
import type { CSSProperties } from "react";
import { color, font, radius, spacing } from "./theme";

export const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  display: "flex",
  justifyContent: "center",
  padding: "2rem 1.5rem",
  fontFamily: font.family,
  backgroundColor: color.bgPage,
  color: color.textPrimary,
};

export const sectionStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: spacing.md,
  padding: spacing.lg,
  border: `0.5px solid ${color.border}`,
  borderRadius: radius.lg,
  backgroundColor: color.bgCard,
};

export const sectionLabelStyle: React.CSSProperties = {
  fontSize: font.size.body,
  fontWeight: 500,
  color: color.textPrimary,
  margin: 0,
};

export const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: spacing.xs,
  fontSize: font.size.body,
  color: color.textSecondary,
  minWidth: 0,
};

export const inputStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: radius.sm,
  border: `0.5px solid ${color.borderField}`,
  backgroundColor: color.bgPage,
  color: color.textPrimary,
  fontSize: font.size.label,
  width: "100%",
  boxSizing: "border-box",
};

export const selectStyle: React.CSSProperties = {
  ...inputStyle,
  appearance: "none",
  backgroundImage:
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%233D4B6E' stroke-width='2.5'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")",
  backgroundRepeat: "no-repeat",
  backgroundPosition: "right 12px center",
  backgroundSize: "16px",
  paddingRight: "36px",
};

export const primaryButtonStyle: React.CSSProperties = {
  padding: "13px",
  borderRadius: radius.md,
  border: "none",
  backgroundColor: color.point,
  color: color.bgPage,
  fontWeight: 500,
  fontSize: font.size.label,
  cursor: "pointer",
};

export const secondaryButtonStyle: React.CSSProperties = {
  padding: "13px 18px",
  borderRadius: radius.md,
  border: `0.5px solid ${color.borderField}`,
  backgroundColor: "transparent",
  color: color.textSecondary,
  fontWeight: 500,
  fontSize: font.size.label,
  cursor: "pointer",
};

export const dangerTextStyle: React.CSSProperties = {
  fontSize: font.size.body,
  color: color.danger,
};

export const cardWrapperStyle: React.CSSProperties = {
  borderRadius: radius.lg,
  overflow: "hidden",
  border: `0.5px solid ${color.border}`,
  backgroundColor: color.bgCard,
};

export const tabHeaderStyle: React.CSSProperties = {
  padding: "12px 16px",
  backgroundColor: color.point,
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
};

export const tabHeaderTextStyle: React.CSSProperties = {
  fontSize: font.size.body,
  fontWeight: 500,
  color: color.bgPage,
};

export const tabHeaderSubTextStyle: React.CSSProperties = {
  fontSize: font.size.small,
  color: color.pointText,
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

export const cardBodyStyle: React.CSSProperties = {
  padding: spacing.lg,
  fontSize: font.size.body,
  color: color.textPrimary,
};

export const toggleTrackStyle = (checked: boolean): React.CSSProperties => ({
  width: "36px",
  height: "20px",
  borderRadius: "999px",
  border: "none",
  padding: "2px",
  cursor: "pointer",
  display: "flex",
  backgroundColor: checked ? color.point : color.borderField,
});

export const toggleKnobStyle = (checked: boolean): React.CSSProperties => ({
  width: "16px",
  height: "16px",
  borderRadius: "50%",
  backgroundColor: color.bgPage,
  transition: "transform 0.15s ease",
  marginLeft: checked ? "auto" : 0,
});

export const statusCardStyle: React.CSSProperties = {
  border: `0.5px solid ${color.border}`,
  borderRadius: radius.lg,
  backgroundColor: color.bgCard,
  padding: "26px 18px",
  textAlign: "center",
};

export const loadingOverlayStyle: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  backgroundColor: "rgba(43, 42, 39, 0.55)",   // color.textPrimary(#2B2A27) 기반 반투명 어두운 톤
  borderRadius: radius.lg,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
};

export const spinnerStyle: React.CSSProperties = {
  width: "32px",
  height: "32px",
  border: `3px solid ${color.border}`,
  borderTopColor: color.point,
  borderRadius: "50%",
  animation: "spin 0.8s linear infinite",
};