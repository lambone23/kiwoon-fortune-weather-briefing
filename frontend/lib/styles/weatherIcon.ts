import {
  IconSun,
  IconCloud,
  IconUmbrella,
  IconSnowflake,
  IconQuestionMark,
} from "@tabler/icons-react";

/**
 * 날씨 문구(백엔드 SKY_MAP/PTY_MAP 기반 텍스트)를 받아
 * 챕터 2(2-8 결론)에서 확정한 아이콘 컴포넌트를 반환.
 * - 구름많음/흐림은 단계 구분 없이 IconCloud 하나로 통일.
 * - 기존 preview/subscribe/manage 3개 화면에 각각 중복돼 있던
 *   skyIcon() 함수를 이 파일 하나로 대체.
 */
export function getWeatherIcon(text: string) {
  if (text.includes("맑음")) return IconSun;
  if (text.includes("비") || text.includes("소나기")) return IconUmbrella;
  if (text.includes("눈")) return IconSnowflake;
  if (text.includes("구름") || text.includes("흐림")) return IconCloud;
  return IconQuestionMark;
}