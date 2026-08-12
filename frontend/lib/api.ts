/**
 * 백엔드(FastAPI) API 호출 함수 모음.
 * - 모든 화면 컴포넌트는 이 파일의 함수만 가져다 쓰고, fetch를 직접 호출하지 않음.
 * - 엔드포인트 주소가 바뀌거나 요청 형식이 바뀌어도 이 파일만 수정하면 됨.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type FortuneRequest = {
  calendar_type: string;
  year: number;
  month: number;
  day: number;
  hour: number | null;   // null이면 "생시 모름" — 백엔드 FortuneRequest.hour(Optional[int])와 일치
  minute: number;
  gender: string;
  region_1: string;
  region_2: string;
};

export type SubscribeRequest = FortuneRequest & {
  email: string;
  region_1: string;
  region_2: string;
  notify_time: string;
  notify_enabled: boolean;
};

export type UpdateSubscriberRequest = Partial<{
  calendar_type: string;
  year: number;
  month: number;
  day: number;
  hour: number | null;
  minute: number;
  gender: string;
  region_1: string;
  region_2: string;
  notify_time: string;
}>;

async function handleResponse(res: Response) {
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "요청 중 문제가 발생했습니다.");
  }
  return data;
}

/** 비로그인 1회성 운세+날씨 조회 */
export async function fetchFortunePreview(req: FortuneRequest) {
  const res = await fetch(`${API_URL}/fortune/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse(res);
}

/** 알림 신청 */
export async function subscribe(req: SubscribeRequest) {
  const res = await fetch(`${API_URL}/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse(res);
}

/** 내 정보 조회 (관리 페이지) */
export async function fetchSubscriberInfo(token: string) {
  const res = await fetch(`${API_URL}/manage/${token}`);
  return handleResponse(res);
}

/** 내 정보 수정 (관리 페이지) */
export async function updateSubscriberInfo(token: string, req: UpdateSubscriberRequest) {
  const res = await fetch(`${API_URL}/manage/${token}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse(res);
}

/** 알림 켜기/끄기 토글 */
export async function toggleNotify(token: string) {
  const res = await fetch(`${API_URL}/manage/${token}/notify`, {
    method: "PATCH",
  });
  return handleResponse(res);
}

/** 관리 링크 재발송 */
export async function resendManageLink(email: string) {
  const res = await fetch(`${API_URL}/manage/resend-link`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return handleResponse(res);
}

/** 시/도 목록 조회 */
export async function fetchRegions() {
  const res = await fetch(`${API_URL}/regions`);
  return handleResponse(res);
}

/** 특정 시/도의 구/군 목록 조회 */
export async function fetchSubRegions(region1: string) {
  const res = await fetch(`${API_URL}/regions/${encodeURIComponent(region1)}`);
  return handleResponse(res);
}

/** 구독 탈퇴 */
export async function deleteSubscriber(token: string) {
  const res = await fetch(`${API_URL}/manage/${token}`, {
    method: "DELETE",
  });
  return handleResponse(res);
}