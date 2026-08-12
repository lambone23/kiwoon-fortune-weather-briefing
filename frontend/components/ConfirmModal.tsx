"use client";

import { IconAlertTriangle, IconHelp } from "@tabler/icons-react";
import type { Icon } from "@tabler/icons-react";
import { color, font, radius, spacing } from "@/lib/styles/theme";
import { secondaryButtonStyle } from "@/lib/styles/common";

type Props = {
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  /** 기본 아이콘(danger 여부로 자동 결정)을 덮어쓰고 싶을 때만 지정 */
  icon?: Icon;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

/**
 * 범용 확인 모달. 9-2 설계 기준:
 * - 배경은 LoadingOverlay와 동일한 어두운 반투명 톤(rgba(43,42,39,0.55))으로
 *   시각적 일관성 유지.
 * - 확인 처리 중(loading=true)일 때는 화면 전체 오버레이를 별도로 띄우지 않고,
 *   확인 버튼 자체가 "처리 중..." 텍스트 + 비활성화로 로딩을 표현함
 *   (레이어가 두 겹으로 겹치는 상황을 구조적으로 방지).
 * - 아이콘은 danger 여부에 따라 기본값이 자동 결정됨:
 *   danger=true → 경고 톤(IconAlertTriangle, color.warningBg/color.danger)
 *   danger=false → 중립 톤(IconHelp, color.bgHighlight/color.point)
 *   다른 상황에서 재사용할 때 icon prop으로 직접 지정도 가능.
 */
export default function ConfirmModal({
  title,
  description,
  confirmLabel = "확인",
  cancelLabel = "취소",
  danger = false,
  icon,
  loading = false,
  onConfirm,
  onCancel,
}: Props) {
  const IconComponent = icon ?? (danger ? IconAlertTriangle : IconHelp);
  const iconBg = danger ? color.warningBg : color.bgHighlight;
  const iconColor = danger ? color.warning : color.point;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(43, 42, 39, 0.55)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: spacing.lg,
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "320px",
          backgroundColor: color.bgCard,
          borderRadius: radius.xl,
          padding: "26px 22px",
          boxSizing: "border-box",
          textAlign: "center",
        }}
      >
        <div
          style={{
            width: "44px",
            height: "44px",
            borderRadius: "50%",
            backgroundColor: iconBg,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 14px",
          }}
        >
          <IconComponent size={20} color={iconColor} aria-hidden="true" />
        </div>

        <p style={{ fontSize: font.size.title, fontWeight: 500, color: color.textPrimary, margin: "0 0 6px" }}>
          {title}
        </p>
        {description && (
        <p style={{ fontSize: font.size.small, color: color.textSecondary, margin: "0 0 20px", lineHeight: 1.6, whiteSpace: "pre-line" }}>
            {description}
        </p>
        )}

        <div style={{ display: "flex", gap: spacing.sm, marginTop: description ? 0 : spacing.lg }}>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            style={{ ...secondaryButtonStyle, flex: 1 }}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            style={{
              flex: 1,
              padding: "12px",
              borderRadius: radius.md,
              border: "none",
              backgroundColor: danger ? color.danger : color.point,
              color: color.bgPage,
              fontSize: font.size.body,
              fontWeight: 500,
              cursor: loading ? "default" : "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "처리 중..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}