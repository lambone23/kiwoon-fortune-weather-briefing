"use client";

import { useEffect } from "react";
import { IconYinYang, IconCalendar, IconClock } from "@tabler/icons-react";
import { color, font, spacing } from "@/lib/styles/theme";
import { sectionStyle, sectionLabelStyle, labelStyle, selectStyle } from "@/lib/styles/common";
import { JIJI_OPTIONS, TIME_UNKNOWN_VALUE, YEAR_OPTIONS, getDaysInMonth, getTodayParts } from "@/lib/saju/timeBranches";

type Props = {
  calendarType: string;
  onCalendarTypeChange: (v: string) => void;
  year: string;
  month: string;
  day: string;
  onYearChange: (v: string) => void;
  onMonthChange: (v: string) => void;
  onDayChange: (v: string) => void;
  timeBranch: string;
  onTimeBranchChange: (v: string) => void;
  gender: string;
  onGenderChange: (v: string) => void;
};

/**
 * 사주 운세를 위한 정보 섹션 (생년월일·시각·성별).
 * 자체 <form>/<fieldset>/로딩 오버레이를 갖지 않는 순수 컨트롤드 컴포넌트 —
 * 반드시 부모의 <form><fieldset disabled={loading}> 안에서 사용할 것.
 *
 * ※ 생년월일 입력은 애초에 <input>+<datalist> 콤보박스(타이핑+선택 겸용)로
 *   시도했으나, <datalist> 드롭다운이 "타이핑(input 이벤트)"에만 반응해서
 *   열리는 브라우저 표준 동작 때문에, 이미 값이 채워진 입력창을 클릭만 하면
 *   목록이 안 열리는 문제가 있어 select로 원복함 (문제 해결 사례로 별도 정리 예정).
 *
 * 미래 날짜 차단: 오늘 날짜(getTodayParts()) 기준으로 연도는 올해까지,
 * 올해가 선택된 경우 월은 이번 달까지, 이번 달까지 선택된 경우 일은
 * 오늘까지만 옵션에 노출됨.
 */
export default function SajuInfoSection({
  calendarType,
  onCalendarTypeChange,
  year,
  month,
  day,
  onYearChange,
  onMonthChange,
  onDayChange,
  timeBranch,
  onTimeBranchChange,
  gender,
  onGenderChange,
}: Props) {
  const today = getTodayParts();
  const isCurrentYear = year === String(today.year);

  // 선택된 연도가 올해면 오늘 월까지만, 아니면 12월까지 전부
  const maxMonth = isCurrentYear ? today.month : 12;
  const monthOptions = Array.from({ length: maxMonth }, (_, i) => i + 1);

  const daysInMonthRaw = getDaysInMonth(year, month);
  const isCurrentYearMonth = isCurrentYear && month === String(today.month);
  // 올해+이번 달이면 오늘 날짜까지만, 아니면 그 달의 실제 마지막 날까지
  const daysInMonth = isCurrentYearMonth ? Math.min(daysInMonthRaw, today.day) : daysInMonthRaw;
  const dayOptions = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  // 연도가 바뀌어서 이미 선택된 월이 미래가 되면(예: 올해로 바꿨는데 12월이 선택돼 있던 경우) 초기화
  useEffect(() => {
    if (month && Number(month) > maxMonth) {
      onMonthChange("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [maxMonth]);

  // 연/월이 바뀌어서 이미 선택된 일이 그 달에 없거나 미래가 되면 초기화
  useEffect(() => {
    if (day && Number(day) > daysInMonth) {
      onDayChange("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [daysInMonth]);

  return (
    <section style={sectionStyle}>
      <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.xs }}>
        <IconYinYang size={16} color={color.point} aria-hidden="true" />
        <span style={sectionLabelStyle}>사주 운세를 위한 정보</span>
      </div>

      <label style={labelStyle}>
        양력/음력
        <select value={calendarType} onChange={(e) => onCalendarTypeChange(e.target.value)} style={selectStyle}>
          <option value="양력">양력</option>
          <option value="음력">음력</option>
        </select>
      </label>

      <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
        <IconCalendar size={16} color={color.point} aria-hidden="true" />
        <span style={{ fontSize: font.size.body, color: color.textSecondary }}>생년월일</span>
      </div>
      <div style={{ display: "flex", gap: spacing.xs }}>
        <select value={year} onChange={(e) => onYearChange(e.target.value)} style={{ ...selectStyle, flex: 1.2 }}>
          <option value="">년도</option>
          {YEAR_OPTIONS.map((y) => (
            <option key={y} value={y}>{y}년</option>
          ))}
        </select>
        <select value={month} onChange={(e) => onMonthChange(e.target.value)} style={{ ...selectStyle, flex: 1 }}>
          <option value="">월</option>
          {monthOptions.map((m) => (
            <option key={m} value={m}>{m}월</option>
          ))}
        </select>
        <select value={day} onChange={(e) => onDayChange(e.target.value)} style={{ ...selectStyle, flex: 1 }}>
          <option value="">일</option>
          {dayOptions.map((d) => (
            <option key={d} value={d}>{d}일</option>
          ))}
        </select>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
        <IconClock size={16} color={color.point} aria-hidden="true" />
        <span style={{ fontSize: font.size.body, color: color.textSecondary }}>태어난 시각</span>
      </div>
      <select value={timeBranch} onChange={(e) => onTimeBranchChange(e.target.value)} style={selectStyle}>
        <option value="">선택하세요</option>
        {JIJI_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.labelKorean} ({opt.labelHanja}) · {opt.range}
          </option>
        ))}
        <option value={TIME_UNKNOWN_VALUE}>시간 모름</option>
      </select>

      <label style={labelStyle}>
        성별
        <select value={gender} onChange={(e) => onGenderChange(e.target.value)} style={selectStyle}>
          <option value="여성">여성</option>
          <option value="남성">남성</option>
        </select>
      </label>
    </section>
  );
}