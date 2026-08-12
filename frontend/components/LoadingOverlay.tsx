"use client";

import { useEffect, useState } from "react";
import { IconSun } from "@tabler/icons-react";
import { color, font, spacing } from "@/lib/styles/theme";
import { loadingOverlayStyle, spinnerStyle } from "@/lib/styles/common";

type Props = {
  messages: string[];
  intervalMs?: number;
};

/**
 * 로딩 오버레이 — 스피너 중앙에 브랜드 아이콘을 얹고, 문구를 일정 간격으로
 * 순환 노출함. common.ts의 loadingOverlayStyle/spinnerStyle을 그대로 재사용.
 * preview/subscribe/manage 화면에서 공통으로 쓸 수 있도록 별도 컴포넌트로 분리.
 */
export default function LoadingOverlay({ messages, intervalMs = 2200 }: Props) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (messages.length <= 1) return;
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % messages.length);
    }, intervalMs);
    return () => clearInterval(timer);
  }, [messages, intervalMs]);

  return (
    <div style={loadingOverlayStyle}>
      <div style={{ position: "relative", width: "32px", height: "32px" }}>
        <div style={spinnerStyle} />
        <IconSun
          size={14}
          color={color.bgPage}
          style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)" }}
          aria-hidden="true"
        />
      </div>
      <p
        style={{
          color: color.bgPage,
          fontSize: font.size.label,
          textAlign: "center",
          padding: "0 24px",
          marginTop: spacing.md,
        }}
      >
        {messages[index]}
      </p>
    </div>
  );
}