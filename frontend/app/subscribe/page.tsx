"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  IconSun,
  IconYinYang,
  IconMail,
  IconClock as IconClockOutline,
  IconTemperature,
  IconCheck,
  IconAlertTriangle,
  IconCopy,
} from "@tabler/icons-react";
import { fetchFortunePreview, fetchRegions, fetchSubRegions, subscribe } from "@/lib/api";
import { color, font, spacing } from "@/lib/styles/theme";
import {
  pageStyle,
  sectionStyle,
  sectionLabelStyle,
  labelStyle,
  inputStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  cardWrapperStyle,
  tabHeaderStyle,
  tabHeaderTextStyle,
  tabHeaderSubTextStyle,
  cardBodyStyle,
  statusCardStyle,
  toggleTrackStyle,
  toggleKnobStyle,
} from "@/lib/styles/common";
import { getWeatherIcon } from "@/lib/styles/weatherIcon";
import { JIJI_OPTIONS, TIME_UNKNOWN_VALUE, getHourFromBranch } from "@/lib/saju/timeBranches";
import SajuInfoSection from "@/components/SajuInfoSection";
import RegionSection from "@/components/RegionSection";
import LoadingOverlay from "@/components/LoadingOverlay";
import { FORTUNE_LOADING_MESSAGES } from "@/lib/loadingMessages";

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
  return {
    date: dateLine,
    temp: tempLine,
    morning: morningLine.replace(/^오전:\s*/, ""),
    afternoon: afternoonLine.replace(/^오후:\s*/, ""),
  };
}

function getTimeBranchLabel(timeBranch: string, withRange: boolean = true): string {
  if (!timeBranch) return "";
  if (timeBranch === TIME_UNKNOWN_VALUE) return "시간 모름";
  const found = JIJI_OPTIONS.find((o) => o.value === timeBranch);
  if (!found) return "";
  return withRange ? `${found.labelKorean}(${found.range})` : found.labelKorean;
}

export default function SubscribePage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [calendarType, setCalendarType] = useState("양력");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [day, setDay] = useState("");
  const [timeBranch, setTimeBranch] = useState("");
  const [gender, setGender] = useState("여성");

  const [region1, setRegion1] = useState("");
  const [region2, setRegion2] = useState("");

  const [notifyTime, setNotifyTime] = useState("07:30");
  const [notifyEnabled, setNotifyEnabled] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [weatherFortune, setWeatherFortune] = useState<{ weather: string; fortune: string } | null>(null);
  const [subscribeResult, setSubscribeResult] = useState<{ message: string; manage_link?: string } | null>(null);

  // /preview에서 넘어온 값 복원 — 챕터7에서 저장한 필드명(year/month/day/timeBranch)과 일치시켜야 함
  useEffect(() => {
    const saved = sessionStorage.getItem("kiwoon_prefill");
    if (!saved) return;

    const data = JSON.parse(saved);
    setCalendarType(data.calendarType ?? "양력");
    setYear(data.year ?? "");
    setMonth(data.month ?? "");
    setDay(data.day ?? "");
    setTimeBranch(data.timeBranch ?? "");
    setGender(data.gender ?? "여성");
    setRegion1(data.region1 ?? "");
    sessionStorage.setItem(
      "kiwoon_pending_region2",
      data.region2 ? JSON.stringify(data.region2) : ""
    );
    sessionStorage.removeItem("kiwoon_prefill");
  }, []);

  const [pendingRegion2, setPendingRegion2] = useState("");
  useEffect(() => {
    const raw = sessionStorage.getItem("kiwoon_pending_region2");
    if (raw) setPendingRegion2(JSON.parse(raw));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!year || !month || !day) return setError("생년월일을 입력해주세요.");
    if (!timeBranch) return setError("태어난 시각을 선택해주세요. 모르신다면 '시간 모름'을 선택해주세요.");
    if (!email) return setError("이메일을 입력해주세요.");
    if (!region1 || !region2) return setError("날씨 조회 지역을 선택해주세요.");

    const hour = getHourFromBranch(timeBranch);
    const payload = {
      calendar_type: calendarType,
      year: Number(year),
      month: Number(month),
      day: Number(day),
      hour,
      minute: 0,
      gender,
      region_1: region1,
      region_2: region2,
    };

  setLoading(true);
  try {
    // ① 먼저 가입 처리 시도 — 이미 가입된 이메일이면 여기서 바로 에러
    const result = await subscribe({
      ...payload,
      email,
      notify_time: notifyTime,
      notify_enabled: notifyEnabled,
    });
    setSubscribeResult(result);

    // ② 가입이 성공했을 때만 미리보기(계산+LLM) 실행
    const preview = await fetchFortunePreview(payload);
    setWeatherFortune({ weather: preview.weather, fortune: preview.fortune });
  } catch (err: any) {
    setError(err.message);
  } finally {
    setLoading(false);
  }

  const fortuneSections = weatherFortune ? parseFortuneSections(weatherFortune.fortune) : null;
  const weatherInfo = weatherFortune ? parseWeatherLines(weatherFortune.weather) : null;
  const isDone = subscribeResult !== null;

  return (
    <main style={pageStyle}>
      <div style={{ width: "100%", maxWidth: "480px" }}>

        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <div
            style={{
              width: "40px", height: "40px", borderRadius: "50%",
              backgroundColor: color.point, display: "flex",
              alignItems: "center", justifyContent: "center", margin: "0 auto 10px",
            }}
          >
            <IconSun size={20} color={color.bgPage} aria-hidden="true" />
          </div>
          <h1 style={{ fontSize: "19px", fontWeight: 500, letterSpacing: "0.5px", color: color.textPrimary, margin: 0 }}>
            KI WOON
          </h1>
          <p style={{ fontSize: font.size.small, color: color.textSecondary, marginTop: "2px" }}>기운</p>
        </div>

        {!isDone && (
          <>
            <h1 style={{ fontSize: font.size.title, fontWeight: 500, color: color.textPrimary, marginBottom: "4px" }}>
              알림 받기
            </h1>
            <p style={{ fontSize: font.size.small, color: color.textSecondary, marginBottom: spacing.xl }}>
              이메일과 정보를 등록하면, 매일 정해진 시간에 오늘의 운세와 날씨를 보내드려요
            </p>

            <div style={{ position: "relative" }}>
              <fieldset disabled={loading} style={{ border: "none", padding: 0, margin: 0 }}>
                <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: spacing.xl }}>

                  <section style={sectionStyle}>
                    <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.xs }}>
                      <IconMail size={16} color={color.point} aria-hidden="true" />
                      <span style={sectionLabelStyle}>알림 받을 이메일</span>
                    </div>
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
                    <p style={{ fontSize: font.size.caption, color: color.textCaption, margin: 0 }}>
                      이메일은 가입 후 변경할 수 없어요. 신중하게 입력해주세요.
                    </p>
                  </section>

                  <section style={sectionStyle}>
                    <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.xs }}>
                      <IconClockOutline size={16} color={color.point} aria-hidden="true" />
                      <span style={sectionLabelStyle}>알림 설정</span>
                    </div>
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
                    <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                      <span style={{ fontSize: font.size.body, color: color.textSecondary }}>매일 알림 받기</span>
                      <button
                        type="button"
                        onClick={() => setNotifyEnabled((prev) => !prev)}
                        style={toggleTrackStyle(notifyEnabled)}
                      >
                        <span style={toggleKnobStyle(notifyEnabled)} />
                      </button>
                      <span style={{ fontSize: font.size.small, color: notifyEnabled ? color.success : color.warning }}>
                        {notifyEnabled ? "On" : "Off"}
                      </span>
                    </div>
                    <p style={{ fontSize: font.size.caption, color: color.textCaption, margin: 0 }}>
                      끄면 알림 없이 정보만 저장돼요. 나중에 관리 링크에서 다시 켤 수 있어요.
                    </p>
                  </section>

                  <SajuInfoSection
                    calendarType={calendarType}
                    onCalendarTypeChange={setCalendarType}
                    year={year}
                    month={month}
                    day={day}
                    onYearChange={setYear}
                    onMonthChange={setMonth}
                    onDayChange={setDay}
                    timeBranch={timeBranch}
                    onTimeBranchChange={setTimeBranch}
                    gender={gender}
                    onGenderChange={setGender}
                  />

                  <RegionSection
                    region1={region1}
                    region2={region2}
                    onRegion1Change={setRegion1}
                    onRegion2Change={setRegion2}
                    pendingRegion2={pendingRegion2}
                    onPendingRegion2Consumed={() => setPendingRegion2("")}
                  />

                  {error && (
                    <p style={{ color: color.danger, fontSize: font.size.body, whiteSpace: "pre-line" }}>
                      {error}
                    </p>
                  )}

                  <div style={{ display: "flex", gap: spacing.sm }}>
                    <button type="button" onClick={() => router.push("/")} disabled={loading} style={secondaryButtonStyle}>
                      처음으로
                    </button>
                    <button type="submit" disabled={loading} style={{ ...primaryButtonStyle, flex: 1 }}>
                      신청하기
                    </button>
                  </div>
                </form>
              </fieldset>

              {loading && <LoadingOverlay messages={FORTUNE_LOADING_MESSAGES} />}
            </div>
          </>
        )}

        {isDone && subscribeResult && weatherInfo && fortuneSections && (() => {
          const MorningIcon = getWeatherIcon(weatherInfo.morning);
          const AfternoonIcon = getWeatherIcon(weatherInfo.afternoon);

          return (
            <div>
              <div style={statusCardStyle}>
                <div
                  style={{
                    width: "48px", height: "48px", borderRadius: "50%",
                    backgroundColor: notifyEnabled ? color.successBg : color.warningBg,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    margin: "0 auto 10px",
                  }}
                >
                  {notifyEnabled
                    ? <IconCheck size={24} color={color.success} aria-hidden="true" />
                    : <IconAlertTriangle size={22} color={color.warning} aria-hidden="true" />}
                </div>
                <p style={{ fontSize: font.size.title, fontWeight: 500, color: color.textPrimary, margin: "0 0 4px" }}>
                  {notifyEnabled ? "신청이 완료됐어요" : "정보만 저장됐어요"}
                </p>
                <p style={{ fontSize: font.size.small, color: color.textSecondary, margin: notifyEnabled ? 0 : "0 0 14px", lineHeight: 1.6 }}>
                  {notifyEnabled
                    ? "확인 메일을 보내드렸어요. 메일함에서 관리 링크를 확인하세요."
                    : "알림 없이 등록되어 메일은 안 가요. 아래 링크로 언제든 관리할 수 있어요."}
                </p>

                {!notifyEnabled && subscribeResult.manage_link && (
                  <>
                    <p style={{ fontSize: font.size.caption, color: color.danger, margin: "0 0 10px" }}>
                      이 링크는 본인 확인용 비밀 링크예요. 공유하지 마세요.
                    </p>
                    <div
                      style={{
                        padding: "9px 10px", borderRadius: "8px", background: color.bgPage,
                        border: `0.5px solid ${color.borderField}`, fontSize: font.size.caption,
                        color: color.textSecondary, overflow: "hidden", textOverflow: "ellipsis",
                        whiteSpace: "nowrap", marginBottom: spacing.sm,
                      }}
                    >
                      {subscribeResult.manage_link}
                    </div>
                    <button
                      onClick={() => navigator.clipboard.writeText(subscribeResult.manage_link!)}
                      style={{ ...secondaryButtonStyle, width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: spacing.xs }}
                    >
                      <IconCopy size={14} aria-hidden="true" />
                      링크 복사하기
                    </button>
                  </>
                )}
              </div>

              <div style={{ ...cardWrapperStyle, marginTop: spacing.md }}>
                <div style={tabHeaderStyle}>
                  <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                    <IconSun size={16} color={color.bgPage} aria-hidden="true" />
                    <span style={tabHeaderTextStyle}>오늘의 날씨</span>
                  </div>
                  <span style={tabHeaderSubTextStyle}>{region1} {region2}</span>
                </div>
                <div style={cardBodyStyle}>
                  <p style={{ margin: `0 0 ${spacing.md} 0`, fontSize: font.size.caption, color: color.textCaption }}>
                    {weatherInfo.date}
                  </p>
                  <div style={{ display: "flex", flexDirection: "column", gap: spacing.sm }}>
                    <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                      <IconTemperature size={16} color={color.point} aria-hidden="true" />
                      <span>{weatherInfo.temp}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                      <MorningIcon size={16} color={color.point} aria-hidden="true" />
                      <span>오전: {weatherInfo.morning}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                      <AfternoonIcon size={16} color={color.point} aria-hidden="true" />
                      <span>오후: {weatherInfo.afternoon}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ ...cardWrapperStyle, marginTop: spacing.md }}>
                <div style={tabHeaderStyle}>
                  <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                    <IconYinYang size={16} color={color.bgPage} aria-hidden="true" />
                    <span style={tabHeaderTextStyle}>오늘의 운세</span>
                  </div>
                  <span style={tabHeaderSubTextStyle}>
                    {year}-{String(month).padStart(2, "0")}-{String(day).padStart(2, "0")}{" "}
                    <span className="time-branch-full">{getTimeBranchLabel(timeBranch, true)}</span>
                    <span className="time-branch-short">{getTimeBranchLabel(timeBranch, false)}</span>
                    , {gender}
                  </span>
                </div>
                <div style={cardBodyStyle}>
                  <div style={{ backgroundColor: color.bgHighlight, borderRadius: "10px", padding: "12px 14px", marginBottom: spacing.lg }}>
                    <p style={{ fontSize: font.size.label, fontWeight: 500, color: color.point, margin: "0 0 4px" }}>총운</p>
                    <p style={{ margin: 0, lineHeight: 1.7 }}>{fortuneSections["총운"]}</p>
                  </div>
                  {["재물운", "학업운", "직업운", "건강운", "연애운"].map((label) => (
                    <div key={label} style={{ marginBottom: "14px" }}>
                      <p style={{ margin: "0 0 4px 0", fontSize: font.size.body, fontWeight: 700, color: color.textPrimary }}>{label}</p>
                      <p style={{ margin: 0, lineHeight: 1.7, fontSize: font.size.body }}>{fortuneSections[label]}</p>
                    </div>
                  ))}
                  <div style={{ borderTop: `0.5px solid ${color.border}`, paddingTop: spacing.md, marginTop: spacing.xs }}>
                    {["행운 컬러", "행운 소재", "행운 방향"].map((label) => (
                      <div key={label} style={{ marginBottom: spacing.md }}>
                        <p style={{ margin: "0 0 4px 0", fontSize: font.size.body, fontWeight: 700, color: color.textPrimary }}>{label}</p>
                        <p style={{ margin: 0, lineHeight: 1.7, fontSize: font.size.body, color: color.textSecondary }}>
                          {fortuneSections[label]}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", gap: spacing.sm, marginTop: spacing.lg }}>
                <button onClick={() => router.push("/")} style={secondaryButtonStyle}>처음으로</button>
                {subscribeResult.manage_link && (
                  <button
                    onClick={() => router.push(subscribeResult.manage_link!.replace(/^https?:\/\/[^/]+/, ""))}
                    style={{ ...primaryButtonStyle, flex: 1 }}
                  >
                    정보 수정하기
                  </button>
                )}
              </div>
            </div>
          );
        })()}

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