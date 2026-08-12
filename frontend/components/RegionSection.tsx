"use client";

import { useEffect, useState } from "react";
import { IconMapPin } from "@tabler/icons-react";
import { color, spacing } from "@/lib/styles/theme";
import { sectionStyle, sectionLabelStyle, selectStyle } from "@/lib/styles/common";
import { fetchRegions, fetchSubRegions } from "@/lib/api";

type Props = {
  region1: string;
  region2: string;
  onRegion1Change: (v: string) => void;
  onRegion2Change: (v: string) => void;
  /** 다른 화면(preview)에서 넘어온 구/군 값을 복원할 때만 사용 (subscribe/manage용) */
  pendingRegion2?: string;
  onPendingRegion2Consumed?: () => void;
};

/**
 * 날씨를 조회할 지역 섹션 (시/도 → 구/군 연동).
 * 지역 목록 fetch(fetchRegions/fetchSubRegions)를 컴포넌트 내부에 캡슐화해서,
 * 화면마다 반복되던 useEffect 두 덩어리를 없앰.
 * 자체 <form>/<fieldset>/로딩 오버레이는 갖지 않음 — SajuInfoSection과 동일 원칙.
 */
export default function RegionSection({
  region1,
  region2,
  onRegion1Change,
  onRegion2Change,
  pendingRegion2,
  onPendingRegion2Consumed,
}: Props) {
  const [regions, setRegions] = useState<string[]>([]);
  const [subRegions, setSubRegions] = useState<string[]>([]);

  useEffect(() => {
    fetchRegions().then((data) => setRegions(data.regions));
  }, []);

  useEffect(() => {
    if (!region1) {
      setSubRegions([]);
      return;
    }
    fetchSubRegions(region1).then((data) => {
      setSubRegions(data.region_2_list);

      if (pendingRegion2 && data.region_2_list.includes(pendingRegion2)) {
        // 다른 화면(preview)에서 넘어온 프리필 값 복원
        onRegion2Change(pendingRegion2);
        onPendingRegion2Consumed?.();
      } else if (region2 && data.region_2_list.includes(region2)) {
        // 이미 선택돼 있던 구/군이 이 시/도에서 여전히 유효하면 그대로 유지
        // (컴포넌트가 재마운트만 됐을 뿐, 사용자가 시/도를 실제로 바꾼 게 아닌 경우)
      } else {
        // 시/도가 실제로 바뀌어서 기존 구/군이 더 이상 유효하지 않은 경우에만 초기화
        onRegion2Change("");
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [region1]);

  return (
    <section style={sectionStyle}>
      <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.xs }}>
        <IconMapPin size={16} color={color.point} aria-hidden="true" />
        <span style={sectionLabelStyle}>날씨를 조회할 지역</span>
      </div>
      <div style={{ display: "flex", gap: spacing.xs }}>
        <select value={region1} onChange={(e) => onRegion1Change(e.target.value)} style={{ ...selectStyle, flex: 1 }}>
          <option value="">시/도</option>
          {regions.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <select
          value={region2}
          onChange={(e) => onRegion2Change(e.target.value)}
          style={{ ...selectStyle, flex: 1 }}
          disabled={!region1}
        >
          <option value="">구/군</option>
          {subRegions.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>
    </section>
  );
}