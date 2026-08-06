"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  fetchSubscriberInfo,
  updateSubscriberInfo,
  toggleNotify,
  deleteSubscriber,
  resendManageLink,
  fetchRegions,
  fetchSubRegions,
} from "@/lib/api";

export default function ManagePage() {
  const router = useRouter();
  const params = useParams<{ token: string }>();
  const token = params.token;

  // ── 초기 조회 상태 ──
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [email, setEmail] = useState("");
  const [originalNotifyEnabled, setOriginalNotifyEnabled] = useState(true);

  // ── 폼 상태 ──
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

  // ── 저장 상태 ──
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [error, setError] = useState("");

  // ── 탈퇴 상태 ──
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleted, setDeleted] = useState(false);

  // ── 재발송(404 화면) 상태 ──
  const [resendEmail, setResendEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState("");

  // 시/도 목록 로드
  useEffect(() => {
    fetchRegions().then((data) => setRegions(data.regions));
  }, []);

  // 최초 조회
  useEffect(() => {
    fetchSubscriberInfo(token)
      .then((data) => {
        setEmail(data.email);
        setCalendarType(data.calendar_type);
        setBirthDate(
          `${data.birth_year}-${String(data.birth_month).padStart(2, "0")}-${String(data.birth_day).padStart(2, "0")}`
        );
        setHour(String(data.birth_hour));
        setMinute(String(data.birth_minute));
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

  // 시/도 선택 시 구/군 연동 (+ 불러온 region2 반영)
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
      } else if (!pendingRegion2) {
        setRegion2((prev) => (data.region_2_list.includes(prev) ? prev : ""));
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

  async function handleSave() {
    setError("");
    setSaveMessage("");

    if (!birthDate) return setError("생년월일을 입력해주세요.");
    if (hour === "") return setError("태어난 시를 입력해주세요.");
    if (!region1 || !region2) return setError("날씨 조회 지역을 선택해주세요.");

    const [year, month, day] = birthDate.split("-").map(Number);
    const minuteValue = minute === "" ? 0 : Number(minute);

    setSaving(true);
    try {
      // ① 알림 토글이 필요하면 먼저 반영 — DB에 최신 상태를 먼저 심어둠
      if (notifyEnabled !== originalNotifyEnabled) {
        await toggleNotify(token);
        setOriginalNotifyEnabled(notifyEnabled);
      }

      // ② 그 다음 정보 수정 — 이 시점엔 notify_enabled가 이미 최신값이라 메일도 정확함
      await updateSubscriberInfo(token, {
        calendar_type: calendarType,
        year, month, day,
        hour: Number(hour),
        minute: minuteValue,
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
        <LogoHeader />

        {loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
            <div style={spinnerStyle} />
          </div>
        )}

        {!loading && notFound && (
          <div>
            <h1 style={titleStyle}>유효하지 않은 링크예요</h1>
            <p style={subtitleStyle}>
              링크가 만료되었거나 잘못된 주소일 수 있어요. 가입하신 이메일로 관리 링크를 다시 받아보세요.
            </p>

            <form onSubmit={handleResend} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
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
              <button type="submit" disabled={resendLoading} style={submitButtonStyle}>
                {resendLoading ? "전송 중..." : "관리 링크 재발송"}
              </button>
              {resendMessage && (
                <p style={{ fontSize: "12px", color: "#c5c2bc" }}>{resendMessage}</p>
              )}
            </form>

            <button
              type="button"
              onClick={() => router.push("/")}
              style={{ ...secondaryButtonStyle, width: "100%", marginTop: "16px" }}
            >
              처음으로
            </button>
          </div>
        )}

        {!loading && !notFound && deleted && (
          <div style={statusCardStyle}>
            <div style={{ ...statusIconWrapStyle, backgroundColor: "rgba(58,166,107,0.15)" }}>
              <span style={{ fontSize: "28px" }}>✅</span>
            </div>
            <p style={statusTitleStyle}>탈퇴가 완료됐어요</p>
            <p style={statusDescStyle}>그동안 이용해주셔서 감사합니다.</p>
            <button
              type="button"
              onClick={() => router.push("/")}
              style={{ ...submitButtonStyle, width: "100%", marginTop: "8px" }}
            >
              처음으로
            </button>
          </div>
        )}

        {!loading && !notFound && !deleted && (
          <div style={{ position: "relative" }}>
            <h1 style={titleStyle}>내 정보 관리</h1>
            <p style={subtitleStyle}>정보를 수정하거나 알림을 켜고 끌 수 있어요</p>

            <fieldset disabled={saving || deleting} style={{ border: "none", padding: 0, margin: 0 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

                <section style={sectionStyle}>
                  <p style={sectionLabelStyle}>📬 등록된 이메일</p>
                  <p style={readOnlyEmailStyle}>{email}</p>
                  <p style={mutedTextStyle}>이메일 변경은 지원하지 않아요. 다른 주소로 받고 싶으면 새로 신청해주세요.</p>
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
                    <span style={{ fontSize: "13px", color: "#c5c2bc" }}>매일 알림 받기</span>
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
                </section>

                {error && <p style={{ color: "#e08080", fontSize: "13px" }}>{error}</p>}
                {saveMessage && <p style={{ color: "#7ed9a3", fontSize: "13px" }}>{saveMessage}</p>}

                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    type="button"
                    onClick={() => router.push("/")}
                    style={secondaryButtonStyle}
                  >
                    처음으로
                  </button>
                  <button
                    type="button"
                    onClick={handleSave}
                    style={{ ...submitButtonStyle, flex: 1 }}
                  >
                    저장하기
                  </button>
                </div>

                {!confirmingDelete && (
                  <button
                    type="button"
                    onClick={() => setConfirmingDelete(true)}
                    style={dangerLinkStyle}
                  >
                    탈퇴하기
                  </button>
                )}

              </div>
            </fieldset>

            <div style={{ marginTop: "24px" }}>
                {confirmingDelete && (
                    <div style={dangerConfirmBoxStyle}>
                    <p style={{ fontSize: "13px", color: "#f5f3ee", fontWeight: 600, margin: 0 }}>
                        정말 탈퇴하시겠어요?
                    </p>
                    <p style={{ fontSize: "12px", color: "#c5c2bc", margin: "6px 0 12px 0" }}>
                        등록된 모든 정보가 즉시 삭제되며, 되돌릴 수 없어요.
                    </p>
                    <div style={{ display: "flex", gap: "8px" }}>
                        <button
                            type="button"
                            onClick={() => setConfirmingDelete(false)}
                            disabled={deleting}
                            style={secondaryButtonStyle}
                            >
                            취소
                        </button>
                        <button
                        type="button"
                        onClick={handleDeleteConfirm}
                        disabled={deleting}
                        style={{ ...dangerButtonStyle, flex: 1 }}
                        >
                        {deleting ? "처리 중..." : "탈퇴 확인"}
                        </button>
                    </div>
                    </div>
                )}
            </div>

            {(saving || deleting) && (
            <div style={loadingOverlayStyle}>
                <div style={spinnerStyle} />
                <p style={{ color: "#f5f3ee", fontSize: "14px", marginTop: "12px" }}>
                {deleting ? "탈퇴 처리 중이에요..." : "저장 중이에요..."}
                </p>
            </div>
            )}
          </div>
        )}
      </div>

      <footer style={{ marginTop: "48px", textAlign: "center" }}>
        <p style={{ fontSize: "12px", color: "#8a8883", margin: 0 }}>문의: lambone234567@gmail.com</p>
        <p style={{ fontSize: "11px", color: "#6a6965", marginTop: "4px" }}>© 2026 Kiwoon. All rights reserved.</p>
      </footer>
    </main>
  );
}

function LogoHeader() {
  return (
    <div style={{ textAlign: "center", marginBottom: "32px" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "center", gap: "8px" }}>
        <span style={{ fontSize: "22px" }}>🌤️</span>
        <h1 style={{ fontSize: "clamp(18px, 5vw, 22px)", fontWeight: 700, letterSpacing: "0.5px", color: "#f5f3ee", margin: 0 }}>
          KI WOON
        </h1>
        <span style={{ fontSize: "clamp(15px, 4vw, 18px)", fontWeight: 500, color: "#c5c2bc" }}>기운</span>
        <span style={{ fontSize: "22px" }}>🔮</span>
      </div>
      <p style={{ fontSize: "12px", color: "#c5c2bc", marginTop: "8px" }}>
        오늘의 날씨(氣)와 사주 운세(運)를 함께 전해드려요
      </p>
      <hr style={{ border: "none", borderTop: "1px solid #5a5955", marginTop: "20px" }} />
    </div>
  );
}

/* ── 스타일: pageStyle ~ tabHeaderSubTextStyle까지는 /preview, /subscribe와 동일 ── */
/* ── toggleRowStyle ~ toggleKnobStyle은 /subscribe와 동일 ── */
/* ── statusCardStyle ~ statusDescStyle은 /subscribe와 동일 ── */

const readOnlyEmailStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: "8px",
  border: "1px solid #5a5955",
  backgroundColor: "#3a3a37",
  color: "#c5c2bc",
  fontSize: "14px",
  margin: 0,
};

const mutedTextStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#8a8883",
  margin: "6px 0 0 0",
};

const dangerLinkStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#c96a6a",
  fontSize: "13px",
  textDecoration: "underline",
  cursor: "pointer",
  padding: "4px 0",
  textAlign: "left",
};

const dangerConfirmBoxStyle: React.CSSProperties = {
  border: "1px solid #8a4a4a",
  borderRadius: "10px",
  backgroundColor: "rgba(201,106,106,0.08)",
  padding: "14px",
};

const dangerButtonStyle: React.CSSProperties = {
  padding: "12px",
  borderRadius: "8px",
  border: "none",
  backgroundColor: "#c96a6a",
  color: "#2a1f1f",
  fontWeight: 700,
  fontSize: "14px",
  cursor: "pointer",
};

const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
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