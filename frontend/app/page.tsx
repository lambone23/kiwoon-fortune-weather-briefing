"use client";

import { useRouter } from "next/navigation";
import { IconSun, IconSearch, IconMail } from "@tabler/icons-react";
import { color, font, radius, spacing } from "@/lib/styles/theme";
import { pageStyle } from "@/lib/styles/common";

export default function Home() {
  const router = useRouter();

  return (
    <main style={pageStyle}>
      <div style={{ width: "100%", maxWidth: "420px" }}>

        <div style={{ textAlign: "center", marginBottom: "36px" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "50%",
              backgroundColor: color.point,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 12px",
            }}
          >
            <IconSun size={22} color={color.bgPage} />
          </div>

          <h1
            style={{
              fontSize: "clamp(20px, 6vw, 24px)",
              fontWeight: 500,
              letterSpacing: "0.5px",
              color: color.textPrimary,
              margin: 0,
            }}
          >
            KI WOON
          </h1>
          <p style={{ fontSize: font.size.small, color: color.textSecondary, marginTop: "2px" }}>
            기운
          </p>

          <p style={{ fontSize: font.size.small, color: color.textSecondary, marginTop: spacing.md, lineHeight: 1.6 }}>
            오늘의 날씨와 사주 운세를 함께 전해드려요
          </p>
          <p style={{ fontSize: font.size.caption, color: color.textCaption, marginTop: spacing.xs, lineHeight: 1.6 }}>
            생년월일시 기반 사주 운세와 지역별 날씨를
            <br />
            매일 이메일로 브리핑해드립니다
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
          <button onClick={() => router.push("/preview")} style={optionCardStyle}>
            <IconSearch size={20} color={color.point} aria-hidden="true" />
            <div style={{ textAlign: "left" }}>
              <div style={{ fontSize: font.size.label, fontWeight: 500, color: color.textPrimary }}>
                바로 결과 보기
              </div>
              <div style={{ fontSize: font.size.small, color: color.textSecondary, marginTop: "2px" }}>
                가입 없이, 지금 한 번만 조회
              </div>
            </div>
          </button>

          <button onClick={() => router.push("/subscribe")} style={optionCardStyle}>
            <IconMail size={20} color={color.point} aria-hidden="true" />
            <div style={{ textAlign: "left" }}>
              <div style={{ fontSize: font.size.label, fontWeight: 500, color: color.textPrimary }}>
                알림 받기
              </div>
              <div style={{ fontSize: font.size.small, color: color.textSecondary, marginTop: "2px" }}>
                이메일로 등록하고 매일 자동으로 받아보기
              </div>
            </div>
          </button>
        </div>

        <footer style={{ marginTop: "48px", textAlign: "center" }}>
          <p style={{ fontSize: font.size.small, color: color.textSecondary, margin: 0 }}>
            문의: lambone234567@gmail.com
          </p>
          <p style={{ fontSize: font.size.caption, color: color.textCaption, marginTop: "4px" }}>
            © 2026 Kiwoon. All rights reserved.
          </p>
        </footer>
      </div>
    </main>
  );
}

// page.tsx 전용 — 다른 화면과 겹치지 않는 스타일이라 common.ts로 옮기지 않음 (3-5 규칙 2번)
const optionCardStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: spacing.md,
  padding: spacing.xl,
  border: `0.5px solid ${color.border}`,
  borderRadius: radius.lg,
  backgroundColor: color.bgCard,
  cursor: "pointer",
  textAlign: "left",
  width: "100%",
};