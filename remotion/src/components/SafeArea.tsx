import { AbsoluteFill } from "remotion";

// دليل المنطقة الآمنة لريلز 1080×1920: الأماكن الحمرا بتغطيها أزرار
// تيك توك وإنستغرام ويوتيوب شورتس. فعّله بـ showSafeArea وقت التصميم بس.
export const SAFE = { top: 220, bottom: 420, side: 80, right: 160 } as const;

export const SafeArea: React.FC = () => {
  const zone = { position: "absolute", background: "rgba(255,0,0,0.25)" } as const;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ ...zone, top: 0, left: 0, right: 0, height: SAFE.top }} />
      <div style={{ ...zone, bottom: 0, left: 0, right: 0, height: SAFE.bottom }} />
      <div style={{ ...zone, top: SAFE.top, bottom: SAFE.bottom, right: 0, width: SAFE.right }} />
      <div style={{ ...zone, top: SAFE.top, bottom: SAFE.bottom, left: 0, width: SAFE.side }} />
    </AbsoluteFill>
  );
};
