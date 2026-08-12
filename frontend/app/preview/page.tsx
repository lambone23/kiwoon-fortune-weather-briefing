"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { IconSun, IconYinYang, IconTemperature } from "@tabler/icons-react";
import { fetchFortunePreview } from "@/lib/api";
import { color, font, spacing } from "@/lib/styles/theme";
import {
  pageStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  cardWrapperStyle,
  tabHeaderStyle,
  tabHeaderTextStyle,
  tabHeaderSubTextStyle,
  cardBodyStyle,
  loadingOverlayStyle,
  spinnerStyle,
} from "@/lib/styles/common";
import { getWeatherIcon } from "@/lib/styles/weatherIcon";
import { FORTUNE_LOADING_MESSAGES } from "@/lib/loadingMessages";
import LoadingOverlay from "@/components/LoadingOverlay";
import { JIJI_OPTIONS, TIME_UNKNOWN_VALUE, getHourFromBranch } from "@/lib/saju/timeBranches";
import SajuInfoSection from "@/components/SajuInfoSection";
import RegionSection from "@/components/RegionSection";

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

function getTimeBranchLabel(timeBranch: string): string {
  if (!timeBranch) return "";
  if (timeBranch === TIME_UNKNOWN_VALUE) return "시간 모름";
  const found = JIJI_OPTIONS.find((o) => o.value === timeBranch);
  return found ? `${found.labelKorean}(${found.range})` : "";
}

export default function PreviewPage() {
  const router = useRouter();

  const [calendarType, setCalendarType] = useState("양력");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [day, setDay] = useState("");
  const [timeBranch, setTimeBranch] = useState("");
  const [gender, setGender] = useState("여성");

  const [region1, setRegion1] = useState("");
  const [region2, setRegion2] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ saju_summary: string; fortune: string; weather: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!year || !month || !day) return setError("생년월일을 입력해주세요.");
    if (!timeBranch) return setError("태어난 시각을 선택해주세요. 모르신다면 '시간 모름'을 선택해주세요.");
    if (!region1 || !region2) return setError("날씨 조회 지역을 선택해주세요.");

    const hour = getHourFromBranch(timeBranch);

    setLoading(true);
    try {
      const data = await fetchFortunePreview({
        calendar_type: calendarType,
        year: Number(year),
        month: Number(month),
        day: Number(day),
        hour,
        minute: 0,
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
      JSON.stringify({ calendarType, year, month, day, timeBranch, gender, region1, region2 })
    );
    router.push("/subscribe");
  }

  const fortuneSections = result ? parseFortuneSections(result.fortune) : null;
  const weatherInfo = result ? parseWeatherLines(result.weather) : null;

  return (
    <main style={pageStyle}>
      <div style={{ width: "100%", maxWidth: "480px" }}>

        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              backgroundColor: color.point,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 10px",
            }}
          >
            <IconSun size={20} color={color.bgPage} aria-hidden="true" />
          </div>
          <h1 style={{ fontSize: "19px", fontWeight: 500, letterSpacing: "0.5px", color: color.textPrimary, margin: 0 }}>
            KI WOON
          </h1>
          <p style={{ fontSize: font.size.small, color: color.textSecondary, marginTop: "2px" }}>기운</p>
          <p style={{ fontSize: font.size.small, color: color.textSecondary, marginTop: spacing.md }}>
            오늘의 날씨와 사주 운세를 함께 전해드려요
          </p>
        </div>

        <h1 style={{ fontSize: font.size.title, fontWeight: 500, color: color.textPrimary, marginBottom: "4px" }}>
          바로 결과 보기
        </h1>
        <p style={{ fontSize: font.size.small, color: color.textSecondary, marginBottom: spacing.xl }}>
          {result
            ? "오늘의 운세와 날씨 결과가 나왔어요"
            : "간단한 정보만 입력하면, 가입 없이 바로 오늘의 운세와 날씨를 확인할 수 있어요"}
        </p>

        {!result && (
          <div style={{ position: "relative" }}>
            <fieldset disabled={loading} style={{ border: "none", padding: 0, margin: 0 }}>
              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: spacing.xl }}>

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
                />

                {error && <p style={{ color: color.danger, fontSize: font.size.body }}>{error}</p>}

                <div style={{ display: "flex", gap: spacing.sm }}>
                  <button type="button" onClick={() => router.push("/")} disabled={loading} style={secondaryButtonStyle}>
                    처음으로
                  </button>
                  <button type="submit" disabled={loading} style={{ ...primaryButtonStyle, flex: 1 }}>
                    오늘의 운세와 날씨 보기
                  </button>
                </div>
              </form>
            </fieldset>

            {loading && <LoadingOverlay messages={FORTUNE_LOADING_MESSAGES} />}
          </div>
        )}

        {result && weatherInfo && fortuneSections && (() => {
          const MorningIcon = getWeatherIcon(weatherInfo.morning);
          const AfternoonIcon = getWeatherIcon(weatherInfo.afternoon);

          return (
            <div>
              <div style={cardWrapperStyle}>
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
                    {year}-{String(month).padStart(2, "0")}-{String(day).padStart(2, "0")} {getTimeBranchLabel(timeBranch)}, {gender}
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
                <button onClick={handleReset} style={secondaryButtonStyle}>다시 조회하기</button>
                <button onClick={handleGoToSubscribe} style={{ ...primaryButtonStyle, flex: 1 }}>알림 신청하러 가기</button>
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