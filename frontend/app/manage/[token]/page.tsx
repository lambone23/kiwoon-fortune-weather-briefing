"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  IconSun,
  IconMail,
  IconClock,
  IconTrash,
} from "@tabler/icons-react";
import {
  fetchSubscriberInfo,
  updateSubscriberInfo,
  toggleNotify,
  deleteSubscriber,
  resendManageLink,
} from "@/lib/api";
import { color, font, spacing } from "@/lib/styles/theme";
import {
  pageStyle,
  sectionStyle,
  sectionLabelStyle,
  labelStyle,
  inputStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  statusCardStyle,
  toggleTrackStyle,
  toggleKnobStyle,
} from "@/lib/styles/common";
import { getBranchFromHour, getHourFromBranch } from "@/lib/saju/timeBranches";
import SajuInfoSection from "@/components/SajuInfoSection";
import RegionSection from "@/components/RegionSection";
import LoadingOverlay from "@/components/LoadingOverlay";
import ConfirmModal from "@/components/ConfirmModal";
import { SAVE_LOADING_MESSAGES } from "@/lib/loadingMessages";

export default function ManagePage() {
  const router = useRouter();
  const params = useParams<{ token: string }>();
  const token = params.token;

  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [email, setEmail] = useState("");
  const [originalNotifyEnabled, setOriginalNotifyEnabled] = useState(true);

  const [calendarType, setCalendarType] = useState("양력");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [day, setDay] = useState("");
  const [timeBranch, setTimeBranch] = useState("");
  const [gender, setGender] = useState("여성");

  const [region1, setRegion1] = useState("");
  const [region2, setRegion2] = useState("");
  const [pendingRegion2, setPendingRegion2] = useState("");

  const [notifyTime, setNotifyTime] = useState("07:30");
  const [notifyEnabled, setNotifyEnabled] = useState(true);

  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [error, setError] = useState("");

  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleted, setDeleted] = useState(false);

  const [resendEmail, setResendEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState("");

  useEffect(() => {
    fetchSubscriberInfo(token)
      .then((data) => {
        setEmail(data.email);
        setCalendarType(data.calendar_type);
        setYear(String(data.birth_year));
        setMonth(String(data.birth_month));
        setDay(String(data.birth_day));
        setTimeBranch(getBranchFromHour(data.birth_hour));
        setGender(data.gender);
        setRegion1(data.region_1);
        setPendingRegion2(data.region_2);
        setNotifyTime(data.notify_time);
        setNotifyEnabled(data.notify_enabled);
        setOriginalNotifyEnabled(data.notify_enabled);
      })
      .catch(() => {
        setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [token]);

  async function handleSave() {
    setError("");
    setSaveMessage("");

    if (!year || !month || !day) return setError("생년월일을 입력해주세요.");
    if (!timeBranch) return setError("태어난 시각을 선택해주세요. 모르신다면 '시간 모름'을 선택해주세요.");
    if (!region1 || !region2) return setError("날씨 조회 지역을 선택해주세요.");

    const hour = getHourFromBranch(timeBranch);

    setSaving(true);
    try {
      if (notifyEnabled !== originalNotifyEnabled) {
        await toggleNotify(token);
        setOriginalNotifyEnabled(notifyEnabled);
      }

      await updateSubscriberInfo(token, {
        calendar_type: calendarType,
        year: Number(year),
        month: Number(month),
        day: Number(day),
        hour,
        minute: 0,
        gender,
        region_1: region1,
        region_2: region2,
        notify_time: notifyTime,
      });

      setSaveMessage("변경사항이 저장되었어요.");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteConfirm() {
    setDeleting(true);
    try {
      await deleteSubscriber(token);
      setDeleted(true);
      setConfirmingDelete(false);
    } catch (err: any) {
      setError(err.message);
      setConfirmingDelete(false);
    } finally {
      setDeleting(false);
    }
  }

  async function handleResend(e: React.FormEvent) {
    e.preventDefault();
    setResendMessage("");
    setResendLoading(true);
    try {
      const data = await resendManageLink(resendEmail);
      setResendMessage(data.message);
    } catch (err: any) {
      setResendMessage(err.message);
    } finally {
      setResendLoading(false);
    }
  }

  return (
    <main style={pageStyle}>
      <div style={{ width: "100%", maxWidth: "480px" }}>

        <div style={{ textAlign: "center", marginBottom: "32px" }}>
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

        {loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
            <div style={{ width: "32px", height: "32px", border: `3px solid ${color.border}`, borderTopColor: color.point, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
          </div>
        )}

        {!loading && notFound && (
          <div>
            <h1 style={{ fontSize: font.size.title, fontWeight: 500, color: color.textPrimary, marginBottom: "6px" }}>
              유효하지 않은 링크예요
            </h1>
            <p style={{ fontSize: font.size.small, color: color.textSecondary, marginBottom: spacing.xl }}>
              링크가 만료되었거나 잘못된 주소일 수 있어요. 가입하신 이메일로 관리 링크를 다시 받아보세요.
            </p>

            <form onSubmit={handleResend} style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
              <label style={labelStyle}>
                이메일
                <input
                  type="email"
                  placeholder="example@email.com"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  style={inputStyle}
                  required
                />
              </label>
              <button type="submit" disabled={resendLoading} style={primaryButtonStyle}>
                {resendLoading ? "전송 중..." : "관리 링크 재발송"}
              </button>
              {resendMessage && (
                <p style={{ fontSize: font.size.caption, color: color.textSecondary }}>{resendMessage}</p>
              )}
            </form>

            <button
              type="button"
              onClick={() => router.push("/")}
              style={{ ...secondaryButtonStyle, width: "100%", marginTop: spacing.lg }}
            >
              처음으로
            </button>
          </div>
        )}

        {!loading && !notFound && deleted && (
          <div style={statusCardStyle}>
            <div style={{ width: "48px", height: "48px", borderRadius: "50%", backgroundColor: color.successBg, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 10px" }}>
              <span style={{ fontSize: "20px", color: color.success }}>✓</span>
            </div>
            <p style={{ fontSize: font.size.title, fontWeight: 500, color: color.textPrimary, margin: "0 0 4px" }}>
              탈퇴가 완료됐어요
            </p>
            <p style={{ fontSize: font.size.small, color: color.textSecondary, margin: 0 }}>
              그동안 이용해주셔서 감사합니다.
            </p>
            <button
              type="button"
              onClick={() => router.push("/")}
              style={{ ...primaryButtonStyle, width: "100%", marginTop: spacing.md }}
            >
              처음으로
            </button>
          </div>
        )}

        {!loading && !notFound && !deleted && (
          <div style={{ position: "relative" }}>
            <h1 style={{ fontSize: font.size.title, fontWeight: 500, color: color.textPrimary, marginBottom: "4px" }}>
              내 정보 관리
            </h1>
            <p style={{ fontSize: font.size.small, color: color.textSecondary, marginBottom: spacing.xl }}>
              정보를 수정하거나 알림을 켜고 끌 수 있어요
            </p>

            <fieldset disabled={saving || deleting} style={{ border: "none", padding: 0, margin: 0 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: spacing.xl }}>

                <section style={sectionStyle}>
                  <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.xs }}>
                    <IconMail size={16} color={color.point} aria-hidden="true" />
                    <span style={sectionLabelStyle}>등록된 이메일</span>
                  </div>
                  <div style={{ padding: "10px 12px", borderRadius: "8px", border: `0.5px solid ${color.borderField}`, background: color.bgPage, color: color.textSecondary, fontSize: font.size.label }}>
                    {email}
                  </div>
                  <p style={{ fontSize: font.size.caption, color: color.textCaption, margin: 0 }}>
                    이메일 변경은 지원하지 않아요. 다른 주소로 받고 싶으면 새로 신청해주세요.
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

                <section style={sectionStyle}>
                  <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.xs }}>
                    <IconClock size={16} color={color.point} aria-hidden="true" />
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
                </section>

                {error && <p style={{ color: color.danger, fontSize: font.size.body }}>{error}</p>}
                {saveMessage && <p style={{ color: color.success, fontSize: font.size.body }}>{saveMessage}</p>}

                <div style={{ display: "flex", gap: spacing.sm }}>
                  <button type="button" onClick={() => router.push("/")} style={secondaryButtonStyle}>
                    처음으로
                  </button>
                  <button type="button" onClick={handleSave} style={{ ...primaryButtonStyle, flex: 1 }}>
                    저장하기
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => setConfirmingDelete(true)}
                  style={{
                    background: "none", border: "none", color: color.danger,
                    fontSize: font.size.body, textDecoration: "underline", cursor: "pointer",
                    padding: "4px 0", textAlign: "left", display: "flex", alignItems: "center", gap: spacing.xs,
                  }}
                >
                  <IconTrash size={14} aria-hidden="true" />
                  탈퇴하기
                </button>
              </div>
            </fieldset>

            {saving && <LoadingOverlay messages={SAVE_LOADING_MESSAGES} />}

            {confirmingDelete && (
              <ConfirmModal
                title="정말 탈퇴하시겠어요?"
                description={"등록된 모든 정보가 즉시 삭제되며,\n되돌릴 수 없어요."}
                confirmLabel="탈퇴하기"
                cancelLabel="취소"
                danger
                loading={deleting}
                onConfirm={handleDeleteConfirm}
                onCancel={() => setConfirmingDelete(false)}
              />
            )}
          </div>
        )}

        <footer style={{ marginTop: "48px", textAlign: "center" }}>
          <p style={{ fontSize: font.size.small, color: color.textSecondary, margin: 0 }}>문의: lambone234567@gmail.com</p>
          <p style={{ fontSize: font.size.caption, color: color.textCaption, marginTop: "4px" }}>© 2026 Kiwoon. All rights reserved.</p>
        </footer>
      </div>
    </main>
  );
}