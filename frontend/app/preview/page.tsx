"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchFortunePreview, fetchRegions, fetchSubRegions } from "@/lib/api";

const FORTUNE_LABELS = ["총운", "재물운", "학업운", "직업운", "건강운", "연애운", "행운 컬러", "행운 소재", "행운 방향"];

function parseFortuneSections(fortuneText: string): Record<string, string> {
  const pattern = new RegExp(`(${FORTUNE_LABELS.join("|")}):\\s*([\\s\\S]*?)(?=(?:${FORTUNE_LABELS.join("|")}):|$)`, "g");
  const result: Record<string, string> = {};
  let match;
  while ((match = pattern.exec(fortuneText)) !== null) {
    result[match[1]] = match[2].trim();
  }
  return result;
}

function parseWeatherLines(weatherText: string) {
  const lines = weatherText.split("\n");
  const dateLine = lines[0] || "";
  const tempLine = lines.find((l) => l.includes("최저")) || "";
  const morningLine = lines.find((l) => l.startsWith("오전")) || "";
  const afternoonLine = lines.find((l) => l.startsWith("오후")) || "";

  function skyIcon(line: string) {
    if (line.includes("맑음")) return "☀️";
    if (line.includes("비") || line.includes("소나기")) return "☔";
    if (line.includes("눈")) return "❄️";
    if (line.includes("구름")) return "⛅";
    if (line.includes("흐림")) return "☁️";
    return "🌡️";
  }

  return {
    date: dateLine,
    temp: tempLine,
    morning: morningLine.replace(/^오전:\s*/, ""),
    afternoon: afternoonLine.replace(/^오후:\s*/, ""),
    morningIcon: skyIcon(morningLine),
    afternoonIcon: skyIcon(afternoonLine),
  };
}

export default function PreviewPage() {
  const router = useRouter();

  const [calendarType, setCalendarType] = useState("양력");
  const [birthDate, setBirthDate] = useState("");
  const [hour, setHour] = useState("");
  const [minute, setMinute] = useState("");
  const [gender, setGender] = useState("여성");

  const [regions, setRegions] = useState<string[]>([]);
  const [region1, setRegion1] = useState("");
  const [subRegions, setSubRegions] = useState<string[]>([]);
  const [region2, setRegion2] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ saju_summary: string; fortune: string; weather: string } | null>(null);

  useEffect(() => {
    fetchRegions().then((data) => setRegions(data.regions));
  }, []);

  useEffect(() => {
    if (!region1) {
      setSubRegions([]);
      setRegion2("");
      return;
    }
    fetchSubRegions(region1).then((data) => {
      setSubRegions(data.region_2_list);
      setRegion2("");
    });
  }, [region1]);

  function handleHourChange(value: string) {
    const onlyDigits = value.replace(/[^0-9]/g, "");
    const num = Number(onlyDigits);
    if (onlyDigits === "" || (num >= 0 && num <= 23)) {
      setHour(onlyDigits);
    }
  }

  function handleMinuteChange(value: string) {
    const onlyDigits = value.replace(/[^0-9]/g, "");
    const num = Number(onlyDigits);
    if (onlyDigits === "" || (num >= 0 && num <= 59)) {
      setMinute(onlyDigits);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
  e.preventDefault();
  setError("");

  if (!birthDate) {
    setError("생년월일을 입력해주세요.");
    return;
  }
  if (hour === "") {
    setError("태어난 시를 입력해주세요.");
    return;
  }

  const [year, month, day] = birthDate.split("-").map(Number);
  const minuteValue = minute === "" ? 0 : Number(minute);

  setLoading(true);
  try {
    const data = await fetchFortunePreview({
      calendar_type: calendarType,
      year,
      month,
      day,
      hour: Number(hour),
      minute: minuteValue,
      gender,
      region_1: region1,
      region_2: region2,
    });
    setResult(data);
  } catch (err: any) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}

  function handleReset() {
    setResult(null);
  }

  function handleGoToSubscribe() {
    sessionStorage.setItem(
      "kiwoon_prefill",
      JSON.stringify({ calendarType, birthDate, hour, minute, gender, region1, region2 })
    );
    router.push("/subscribe");
  }

  const fortuneSections = result ? parseFortuneSections(result.fortune) : null;
  const weatherInfo = result ? parseWeatherLines(result.weather) : null;
  const mainFortuneItems = ["재물운", "학업운", "직업운", "건강운", "연애운"];
  const luckItems: { label: string; icon: string }[] = [
    { label: "행운 컬러", icon: "🎨" },
    { label: "행운 소재", icon: "🧵" },
    { label: "행운 방향", icon: "🧭" },
  ];

  return (
    <main style={pageStyle}>
      <div style={{ width: "100%", maxWidth: "480px" }}>

        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "center", gap: "8px" }}>
            <span style={{ fontSize: "22px" }}>🌤️</span>
            <h1 style={{ fontSize: "clamp(18px, 5vw, 22px)", fontWeight: 700, letterSpacing: "0.5px", color: "#f5f3ee", margin: 0 }}>
              KI WOON
            </h1>
            <span style={{ fontSize: "clamp(15px, 4vw, 18px)", fontWeight: 500, color: "#c5c2bc" }}>
              기운
            </span>
            <span style={{ fontSize: "22px" }}>🔮</span>
          </div>

          <p style={{ fontSize: "12px", color: "#c5c2bc", marginTop: "8px" }}>
            오늘의 날씨(氣)와 사주 운세(運)를 함께 전해드려요
          </p>

          <hr style={{ border: "none", borderTop: "1px solid #5a5955", marginTop: "20px" }} />
        </div>
        <h1 style={titleStyle}>바로 결과 보기</h1>
        <p style={subtitleStyle}>
          {result
            ? "오늘의 운세와 날씨 결과가 나왔어요"
            : "간단한 정보만 입력하면, 가입 없이 바로 오늘의 운세와 날씨를 확인할 수 있어요"}
        </p>

        {!result && (
          <div style={{ position: "relative" }}>
            <fieldset disabled={loading} style={{ border: "none", padding: 0, margin: 0 }}>
              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

                <section style={sectionStyle}>
                  <p style={sectionLabelStyle}>🔮 사주 운세를 위한 정보</p>

                  <label style={labelStyle}>
                    양력/음력
                    <select value={calendarType} onChange={(e) => setCalendarType(e.target.value)} style={selectStyle}>
                      <option value="양력">양력</option>
                      <option value="음력">음력</option>
                    </select>
                  </label>

                  <label style={labelStyle}>
                    생년월일
                    <input
                      type="date"
                      min="1900-01-01"
                      max="2030-12-31"
                      value={birthDate}
                      onChange={(e) => setBirthDate(e.target.value)}
                      style={inputStyle}
                      required
                    />
                  </label>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <label style={{ ...labelStyle, flex: 1 }}>
                      태어난 시 (0~23)
                      <input
                        type="number"
                        min={0}
                        max={23}
                        placeholder="시 (예: 23시)"
                        value={hour}
                        onChange={(e) => handleHourChange(e.target.value)}
                        style={inputStyle}
                        required
                      />
                    </label>
                    <label style={{ ...labelStyle, flex: 1 }}>
                      분 (0~59)
                      <input
                        type="number"
                        min={0}
                        max={59}
                        placeholder="분 (예: 10분)"
                        value={minute}
                        onChange={(e) => handleMinuteChange(e.target.value)}
                        style={inputStyle}
                        required
                      />
                    </label>
                  </div>

                  <label style={labelStyle}>
                    성별
                    <select value={gender} onChange={(e) => setGender(e.target.value)} style={selectStyle}>
                      <option value="여성">여성</option>
                      <option value="남성">남성</option>
                    </select>
                  </label>
                </section>

                <section style={sectionStyle}>
                  <p style={sectionLabelStyle}>☀️ 오늘의 날씨를 조회할 지역 정보</p>

                  <label style={labelStyle}>
                    시/도
                    <select value={region1} onChange={(e) => setRegion1(e.target.value)} style={selectStyle} required>
                      <option value="">선택하세요</option>
                      {regions.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </label>

                  <label style={labelStyle}>
                    구/군
                    <select
                      value={region2}
                      onChange={(e) => setRegion2(e.target.value)}
                      style={selectStyle}
                      required
                      disabled={!region1}
                    >
                      <option value="">선택하세요</option>
                      {subRegions.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </label>
                </section>

                {error && <p style={{ color: "#e08080", fontSize: "13px" }}>{error}</p>}

                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    type="button"
                    onClick={() => router.push("/")}
                    disabled={loading}
                    style={secondaryButtonStyle}
                  >
                    처음으로
                  </button>
                  <button type="submit" disabled={loading} style={{ ...submitButtonStyle, flex: 1 }}>
                    오늘의 운세와 날씨 보기
                  </button>
                </div>
              </form>
            </fieldset>

            {loading && (
              <div style={loadingOverlayStyle}>
                <div style={spinnerStyle} />
                <p style={{ color: "#f5f3ee", fontSize: "14px", marginTop: "12px" }}>
                  조회 중이에요...
                </p>
              </div>
            )}
          </div>
        )}

        {result && weatherInfo && fortuneSections && (
          <div>
            {/* 날씨 카드 */}
            <div style={cardWrapperStyle}>
              <div style={{ ...tabHeaderStyle, backgroundColor: "#4a90d9" }}>
                <div style={tabHeaderRowStyle}>
                  <span style={tabHeaderTextStyle}>☀️ 오늘의 날씨</span>
                  <span style={tabHeaderSubTextStyle}>{region1} {region2}</span>
                </div>
              </div>
              <div style={cardBodyStyle}>
                <p style={{ margin: "0 0 10px 0", fontSize: "12px", color: "#a8a5a0" }}>{weatherInfo.date}</p>
                <ul style={listStyle}>
                  <li style={listItemStyle}>
                    <span style={{ marginRight: "8px" }}>🌡️</span>
                    {weatherInfo.temp}
                  </li>
                  <li style={listItemStyle}>
                    <span style={{ marginRight: "8px" }}>{weatherInfo.morningIcon}</span>
                    오전: {weatherInfo.morning}
                  </li>
                  <li style={listItemStyle}>
                    <span style={{ marginRight: "8px" }}>{weatherInfo.afternoonIcon}</span>
                    오후: {weatherInfo.afternoon}
                  </li>
                </ul>
              </div>
            </div>

            {/* 운세 카드 */}
            <div style={{ ...cardWrapperStyle, marginTop: "12px" }}>
              <div style={{ ...tabHeaderStyle, backgroundColor: "#8a5cd9" }}>
                <div style={tabHeaderRowStyle}>
                  <span style={tabHeaderTextStyle}>🔮 오늘의 운세</span>
                  <span style={tabHeaderSubTextStyle}>
                    {birthDate} {hour.padStart(2, "0")}:{(minute || "0").padStart(2, "0")}, {gender}
                  </span>
                </div>
              </div>
              <div style={cardBodyStyle}>
                <div style={totalFortuneBoxStyle}>
                  <p style={totalFortuneLabelStyle}>✨ 총운</p>
                  <p style={{ margin: 0, lineHeight: 1.7 }}>{fortuneSections["총운"]}</p>
                </div>

                {mainFortuneItems.map((label) => (
                  <div key={label} style={{ marginBottom: "14px" }}>
                    <p style={fortuneItemLabelStyle}>{label}</p>
                    <p style={{ margin: 0, lineHeight: 1.7, fontSize: "13px" }}>{fortuneSections[label]}</p>
                  </div>
                ))}

                <div style={luckDividerStyle}>
                  {luckItems.map(({ label, icon }) => (
                    <div key={label} style={{ marginBottom: "12px" }}>
                      <p style={luckLabelStyle}>{icon} {label}</p>
                      <p style={{ margin: 0, lineHeight: 1.7, fontSize: "13px", color: "#c5c2bc" }}>
                        {fortuneSections[label]}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
              <button onClick={handleReset} style={secondaryButtonStyle}>
                다시 조회하기
              </button>
              <button onClick={handleGoToSubscribe} style={{ ...submitButtonStyle, flex: 1 }}>
                알림 신청하러 가기
              </button>
            </div>
          </div>
        )}
            <footer style={{ marginTop: "48px", textAlign: "center" }}>
        <p style={{ fontSize: "12px", color: "#8a8883", margin: 0 }}>
          문의: lambone234567@gmail.com
        </p>
        <p style={{ fontSize: "11px", color: "#6a6965", marginTop: "4px" }}>
          © 2026 Kiwoon. All rights reserved.
        </p>
      </footer>
      
      </div>

    </main>
   
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  display: "flex",
  justifyContent: "center",
  padding: "2rem 1.5rem",
  fontFamily: "'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif",
  backgroundColor: "#3a3a37",
  color: "#e8e6e0",
};

const titleStyle: React.CSSProperties = {
  fontSize: "20px",
  fontWeight: 700,
  color: "#f5f3ee",
  marginBottom: "6px",
};

const subtitleStyle: React.CSSProperties = {
  fontSize: "13px",
  color: "#c5c2bc",
  marginBottom: "20px",
};

const sectionStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "12px",
  padding: "16px",
  border: "1px solid #5a5955",
  borderRadius: "12px",
  backgroundColor: "#42413e",
};

const sectionLabelStyle: React.CSSProperties = {
  fontSize: "13px",
  fontWeight: 600,
  color: "#f5f3ee",
  margin: 0,
};

const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "6px",
  fontSize: "13px",
  color: "#c5c2bc",
  minWidth: 0,
};

const inputStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: "8px",
  border: "1px solid #5a5955",
  backgroundColor: "#4d4c48",
  color: "#f5f3ee",
  fontSize: "14px",
  width: "100%",
  boxSizing: "border-box",
  colorScheme: "dark",
};

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  appearance: "none",
  backgroundImage:
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23f5f3ee' stroke-width='2.5'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")",
  backgroundRepeat: "no-repeat",
  backgroundPosition: "right 12px center",
  backgroundSize: "16px",
  paddingRight: "36px",
};

const submitButtonStyle: React.CSSProperties = {
  padding: "14px",
  borderRadius: "10px",
  border: "none",
  backgroundColor: "#e8e6e0",
  color: "#262624",
  fontWeight: 600,
  fontSize: "15px",
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  padding: "14px 18px",
  borderRadius: "10px",
  border: "1px solid #5a5955",
  backgroundColor: "transparent",
  color: "#e8e6e0",
  fontWeight: 600,
  fontSize: "15px",
  cursor: "pointer",
};

const cardWrapperStyle: React.CSSProperties = {
  borderRadius: "12px",
  overflow: "hidden",
  border: "1px solid #5a5955",
};

const tabHeaderStyle: React.CSSProperties = {
  padding: "10px 16px",
};

const tabHeaderTextStyle: React.CSSProperties = {
  fontSize: "14px",
  fontWeight: 600,
  color: "#ffffff",
};

const cardBodyStyle: React.CSSProperties = {
  backgroundColor: "#4d4c48",
  padding: "16px",
  fontSize: "13px",
  color: "#e8e6e0",
};

const listStyle: React.CSSProperties = {
  listStyle: "none",
  margin: 0,
  padding: 0,
  display: "flex",
  flexDirection: "column",
  gap: "8px",
};

const listItemStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  fontSize: "13px",
  lineHeight: 1.5,
};

const totalFortuneBoxStyle: React.CSSProperties = {
  backgroundColor: "#5c4a80",
  borderRadius: "10px",
  padding: "12px 14px",
  marginBottom: "16px",
};

const totalFortuneLabelStyle: React.CSSProperties = {
  margin: "0 0 4px 0",
  fontSize: "14px",
  fontWeight: 600,
  color: "#e8ddff",
};

const fortuneItemLabelStyle: React.CSSProperties = {
  margin: "0 0 4px 0",
  fontSize: "13px",
  fontWeight: 700,
  color: "#f5f3ee",
};

const luckDividerStyle: React.CSSProperties = {
  borderTop: "1px solid #5a5955",
  paddingTop: "12px",
  marginTop: "4px",
};

const luckLabelStyle: React.CSSProperties = {
  margin: "0 0 4px 0",
  fontSize: "13px",
  fontWeight: 700,
  color: "#f5f3ee",
};

const loadingOverlayStyle: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  backgroundColor: "rgba(38, 38, 36, 0.75)",
  borderRadius: "12px",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
};

const spinnerStyle: React.CSSProperties = {
  width: "32px",
  height: "32px",
  border: "3px solid #5a5955",
  borderTopColor: "#e8e6e0",
  borderRadius: "50%",
  animation: "spin 0.8s linear infinite",
};

const tabHeaderRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "8px",
};

const tabHeaderSubTextStyle: React.CSSProperties = {
  fontSize: "12px",
  fontWeight: 400,
  color: "rgba(255,255,255,0.85)",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};