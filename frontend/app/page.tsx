"use client";

import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
        fontFamily: "'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif",
        backgroundColor: "#3a3a37",
        color: "#e8e6e0",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: "36px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "center",
            gap: "8px",
          }}
        >
          <span style={{ fontSize: "26px" }}>🌤️</span>
          <h1
            style={{
              fontSize: "clamp(22px, 6vw, 28px)",
              fontWeight: 700,
              letterSpacing: "0.5px",
              color: "#f5f3ee",
              margin: 0,
            }}
          >
            KI WOON
          </h1>
          <span
            style={{
              fontSize: "clamp(18px, 5vw, 22px)",
              fontWeight: 500,
              color: "#c5c2bc",
            }}
          >
            기운
          </span>
          <span style={{ fontSize: "26px" }}>🔮</span>
        </div>

        <p style={{ fontSize: "13px", color: "#c5c2bc", marginTop: "10px" }}>
          오늘의 날씨(氣)와 사주 운세(運)를 함께 전해드려요
        </p>

        <p style={{ fontSize: "12px", color: "#8a8883", marginTop: "6px", lineHeight: 1.6 }}>
          생년월일시 기반 사주 운세와 지역별 날씨를
          <br />
          매일 이메일로 브리핑해드립니다
        </p>
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "14px",
          width: "100%",
          maxWidth: "420px",
        }}
      >
        <button onClick={() => router.push("/preview")} style={cardButtonStyle}>
          <span style={{ fontSize: "26px" }}>🔍</span>
          <div style={{ textAlign: "left" }}>
            <div style={{ fontSize: "17px", fontWeight: 600, color: "#f5f3ee" }}>
              바로 결과 보기
            </div>
            <div style={{ fontSize: "14px", color: "#c5c2bc", marginTop: "2px" }}>
              가입 없이, 지금 한 번만 조회
            </div>
          </div>
        </button>

        <button onClick={() => router.push("/subscribe")} style={cardButtonStyle}>
          <span style={{ fontSize: "26px" }}>📬</span>
          <div style={{ textAlign: "left" }}>
            <div style={{ fontSize: "17px", fontWeight: 600, color: "#f5f3ee" }}>
              알림 받기
            </div>
            <div style={{ fontSize: "14px", color: "#c5c2bc", marginTop: "2px" }}>
              이메일로 등록하고 매일 자동으로 받아보기
            </div>
          </div>
        </button>
      </div>

      <footer style={{ marginTop: "48px", textAlign: "center" }}>
        <p style={{ fontSize: "12px", color: "#8a8883", margin: 0 }}>
          문의: lambone234567@gmail.com
        </p>
        <p style={{ fontSize: "11px", color: "#6a6965", marginTop: "4px" }}>
          © 2026 Kiwoon. All rights reserved.
        </p>
      </footer>
    </main>
  );
}

const cardButtonStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "14px",
  padding: "20px",
  border: "1px solid #5a5955",
  borderRadius: "14px",
  backgroundColor: "#4d4c48",
  cursor: "pointer",
  textAlign: "left",
  width: "100%",
};