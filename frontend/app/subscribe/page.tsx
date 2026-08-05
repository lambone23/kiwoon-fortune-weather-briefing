"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  fetchFortunePreview,
  fetchRegions,
  fetchSubRegions,
  subscribe,
} from "@/lib/api";

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
    if (line.includes("비") || line.includes("소나기")) return "🌧️";
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

export default function SubscribePage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [calendarType, setCalendarType] = useState("양력");
  const [birthDate, setBirthDate] = useState("");
  const [hour, setHour] = useState("");
  const [minute, setMinute] = useState("");
  const [gender, setGender] = useState("여성");

  const [regions, setRegions] = useState<string[]>([]);
  const [region1, setRegion1] = useState("");
  const [subRegions, setSubRegions] = useState<string[]>([]);
  const [region2, setRegion2] = useState("");
  const [pendingRegion2, setPendingRegion2] = useState("");

  const [notifyTime, setNotifyTime] = useState("07:30");
  const [notifyEnabled, setNotifyEnabled] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [weatherFortune, setWeatherFortune] = useState<{ weather: string; fortune: string } | null>(null);
  const [subscribeResult, setSubscribeResult] = useState<{ message: string; manage_link?: string } | null>(null);

  // 시/도 목록 로드
  useEffect(() => {
    fetchRegions().then((data) => setRegions(data.regions));
  }, []);

  // /preview에서 넘어온 값 복원
  useEffect(() => {
    const saved = sessionStorage.getItem("kiwoon_prefill");
    if (!saved) return;

    const data = JSON.parse(saved);
    setCalendarType(data.calendarType);
    setBirthDate(data.birthDate);
    setHour(data.hour);
    setMinute(data.minute);
    setGender(data.gender);
    setRegion1(data.region1);
    setPendingRegion2(data.region2);
    sessionStorage.removeItem("kiwoon_prefill");
  }, []);

  // 시/도 선택 시 구/군 연동 (+ 이어받은 region2 반영)
  useEffect(() => {
    if (!region1) {
      setSubRegions([]);
      setRegion2("");
      return;
    }
    fetchSubRegions(region1).then((data) => {
      setSubRegions(data.region_2_list);
      if (pendingRegion2 && data.region_2_list.includes(pendingRegion2)) {
        setRegion2(pendingRegion2);
        setPendingRegion2("");
      } else {
        setRegion2("");
      }
    });
  }, [region1]);

  function handleHourChange(value: string) {
    const onlyDigits = value.replace(/[^0-9]/g, "");
    const num = Number(onlyDigits);
    if (onlyDigits === "" || (num >= 0 && num <= 23)) setHour(onlyDigits);
  }

  function handleMinuteChange(value: string) {
    const onlyDigits = value.replace(/[^0-9]/g, "");
    const num = Number(onlyDigits);
    if (onlyDigits === "" || (num >= 0 && num <= 59)) setMinute(onlyDigits);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!birthDate) return setError("생년월일을 입력해주세요.");
    if (hour === "") return setError("태어난 시를 입력해주세요.");
    if (!email) return setError("이메일을 입력해주세요.");
    if (!region1 || !region2) return setError("날씨 조회 지역을 선택해주세요.");

    const [year, month, day] = birthDate.split("-").map(Number);
    const minuteValue = minute === "" ? 0 : Number(minute);

    const payload = {
      calendar_type: calendarType,
      year,
      month,
      day,
      hour: Number(hour),
      minute: minuteValue,
      gender,
      region_1: region1,
      region_2: region2,
    };

    setLoading(true);
    try {
      // ① 화면 표시용 날씨/운세
      const preview = await fetchFortunePreview(payload);
      setWeatherFortune({ weather: preview.weather, fortune: preview.fortune });

      // ② 실제 구독 등록
      const result = await subscribe({
        ...payload,
        email,
        notify_time: notifyTime,
        notify_enabled: notifyEnabled,
      });
      setSubscribeResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const fortuneSections = weatherFortune ? parseFortuneSections(weatherFortune.fortune) : null;
  const weatherInfo = weatherFortune ? parseWeatherLines(weatherFortune.weather) : null;
  const mainFortuneItems = ["재물운", "학업운", "직업운", "건강운", "연애운"];
  const luckItems: { label: string; icon: string }[] = [
    { label: "행운 컬러", icon: "🎨" },
    { label: "행운 소재", icon: "🧵" },
    { label: "행운 방향", icon: "🧭" },
  ];

  const isDone = subscribeResult !== null;

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
        {!isDone && (
          <>
            <h1 style={titleStyle}>알림 받기</h1>
            <p style={subtitleStyle}>
              이메일과 정보를 등록하면, 매일 정해진 시간에 오늘의 운세와 날씨를 보내드려요
            </p>

            <div style={{ position: "relative" }}>
              <fieldset disabled={loading} style={{ border: "none", padding: 0, margin: 0 }}>
                <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

                  <section style={sectionStyle}>
                    <p style={sectionLabelStyle}>📬 알림 받을 이메일</p>
                    <label style={labelStyle}>
                      이메일
                      <input
                        type="email"
                        placeholder="example@email.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        style={inputStyle}
                        required
                      />
                    </label>
                    <p style={{ fontSize: "11px", color: "#8a8883", margin: 0 }}>
                    ⚠️ 이메일은 가입 후 변경할 수 없어요. 신중하게 입력해주세요.
                    </p>
                  </section>




                  <section style={sectionStyle}>
                    <p style={sectionLabelStyle}>⏰ 알림 설정</p>

                    <label style={labelStyle}>
                      알림 받을 시간
                      <input
                        type="time"
                        value={notifyTime}
                        onChange={(e) => setNotifyTime(e.target.value)}
                        style={inputStyle}
                        required
                      />
                    </label>

                    <div style={toggleRowStyle}>
                      <span style={{ fontSize: "13px", color: "#c5c2bc" }}>
                        매일 알림 받기
                      </span>
                      <button
                        type="button"
                        onClick={() => setNotifyEnabled((prev) => !prev)}
                        style={{
                          ...toggleButtonStyle,
                          backgroundColor: notifyEnabled ? "#3aa66b" : "#5a5955",
                        }}
                      >
                        <span
                          style={{
                            ...toggleKnobStyle,
                            transform: notifyEnabled ? "translateX(18px)" : "translateX(0)",
                          }}
                        />
                      </button>
                      <span style={{ fontSize: "12px", color: notifyEnabled ? "#7ed9a3" : "#c99a5a" }}>
                        {notifyEnabled ? "On" : "Off"}
                      </span>
                    </div>
                    <p style={{ fontSize: "11px", color: "#8a8883", margin: 0 }}>
                      끄면 알림 없이 정보만 저장돼요. 나중에 관리 링크에서 다시 켤 수 있어요.
                    </p>
                  </section>





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
                    <p style={sectionLabelStyle}>☀️ 날씨를 조회할 지역 정보</p>

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
                      신청하기
                    </button>
                  </div>
                </form>
              </fieldset>

              {loading && (
                <div style={loadingOverlayStyle}>
                  <div style={spinnerStyle} />
                  <p style={{ color: "#f5f3ee", fontSize: "14px", marginTop: "12px" }}>
                    신청 처리 중이에요...
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {isDone && subscribeResult && weatherInfo && fortuneSections && (
          <div>
            <p style={doneHeaderStyle}>
              신청 완료 · 알림 {notifyEnabled ? "ON" : "OFF"}
            </p>

            {/* 알림 상태 카드 */}
            <div style={statusCardStyle}>
              <div
                style={{
                  ...statusIconWrapStyle,
                  backgroundColor: notifyEnabled ? "rgba(58,166,107,0.15)" : "rgba(201,154,90,0.15)",
                }}
              >
                <span style={{ fontSize: "28px" }}>{notifyEnabled ? "✅" : "⚠️"}</span>
              </div>
              <p style={statusTitleStyle}>
                {notifyEnabled ? "신청이 완료됐어요" : "정보만 저장됐어요"}
              </p>
              <p style={statusDescStyle}>
                {notifyEnabled
                  ? "확인 메일을 보내드렸어요. 메일함에서 관리 링크를 확인하세요."
                  : "알림 없이 등록되어 메일은 안 갑니다."}
              </p>

                {notifyEnabled && (
                <p style={{ ...warningTextStyle, marginTop: "-10px" }}>
                    🔒 관리 링크는 본인 확인용 비밀 링크예요. 다른 사람에게 공유하지 마세요.
                </p>
                )}

                {!notifyEnabled && (
                <p style={{ ...warningTextStyle, marginTop: "-10px" }}>
                    🔒 이 링크는 본인 확인용 비밀 링크예요. 다른 사람에게 공유하지 마세요.
                </p>
                )}

                {!notifyEnabled && subscribeResult.manage_link && (
                <>
                    <div style={{ ...linkBoxStyle, marginTop: "12px" }}>{subscribeResult.manage_link}</div>
                    <button
                    onClick={() => navigator.clipboard.writeText(subscribeResult.manage_link!)}
                    style={copyButtonStyle}
                    >
                    📋 링크 복사하기
                    </button>
                </>
                )}
            </div>

            {/* 날씨 카드 */}
            <div style={{ ...cardWrapperStyle, marginTop: "16px" }}>
              <div style={{ ...tabHeaderStyle, backgroundColor: "#4a90d9" }}>
                <div style={tabHeaderRowStyle}>
                  <span style={tabHeaderTextStyle}>☀️ 오늘의 날씨</span>
                  <span style={tabHeaderSubTextStyle}>{region1} {region2}</span>
                </div>
              </div>
              <div style={cardBodyStyle}>
                <p style={{ margin: "0 0 10px 0", fontSize: "12px", color: "#a8a5a0" }}>{weatherInfo.date}</p>
                <ul style={listStyle}>
                  <li style={listItemStyle}><span style={{ marginRight: "8px" }}>🌡️</span>{weatherInfo.temp}</li>
                  <li style={listItemStyle}><span style={{ marginRight: "8px" }}>{weatherInfo.morningIcon}</span>오전: {weatherInfo.morning}</li>
                  <li style={listItemStyle}><span style={{ marginRight: "8px" }}>{weatherInfo.afternoonIcon}</span>오후: {weatherInfo.afternoon}</li>
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
            <button onClick={() => router.push("/")} style={secondaryButtonStyle}>
                처음으로
            </button>
            {subscribeResult.manage_link && (
                <button
                onClick={() =>
                    router.push(subscribeResult.manage_link!.replace(/^https?:\/\/[^/]+/, ""))
                }
                style={{ ...submitButtonStyle, flex: 1 }}
                >
                정보 수정하기
                </button>
            )}
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

/* ── 스타일: pageStyle ~ tabHeaderSubTextStyle까지는 /preview/page.tsx와 완전 동일 (생략) ── */

const doneHeaderStyle: React.CSSProperties = {
  fontSize: "13px",
  color: "#c5c2bc",
  marginBottom: "12px",
};

const statusCardStyle: React.CSSProperties = {
  border: "1px solid #5a5955",
  borderRadius: "14px",
  backgroundColor: "#4d4c48",
  padding: "28px 20px",
  textAlign: "center",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: "10px",
};

const statusIconWrapStyle: React.CSSProperties = {
  width: "56px",
  height: "56px",
  borderRadius: "50%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const statusTitleStyle: React.CSSProperties = {
  fontSize: "17px",
  fontWeight: 700,
  color: "#f5f3ee",
  margin: 0,
};

const statusDescStyle: React.CSSProperties = {
  fontSize: "13px",
  color: "#c5c2bc",
  margin: 0,
  lineHeight: 1.6,
};

const linkBoxStyle: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "8px",
  backgroundColor: "#3a3a37",
  border: "1px solid #5a5955",
  fontSize: "12px",
  color: "#c5c2bc",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  marginTop: "8px",
};

const copyButtonStyle: React.CSSProperties = {
  width: "100%",
  padding: "12px",
  borderRadius: "8px",
  border: "1px solid #5a5955",
  backgroundColor: "transparent",
  color: "#f5f3ee",
  fontSize: "14px",
  fontWeight: 600,
  cursor: "pointer",
  marginTop: "8px",
};

const toggleRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
};

const toggleButtonStyle: React.CSSProperties = {
  width: "40px",
  height: "22px",
  borderRadius: "999px",
  border: "none",
  padding: "2px",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
};

const toggleKnobStyle: React.CSSProperties = {
  width: "18px",
  height: "18px",
  borderRadius: "50%",
  backgroundColor: "#f5f3ee",
  transition: "transform 0.15s ease",
};

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

const warningTextStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#c99a5a",
  margin: 0,
  lineHeight: 1.5,
};