import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT_UI } from "../theme/fonts";
import type { Theme } from "../theme/themes";

// مؤقت دائري: الحلقة بتفضى مع الوقت والرقم بنبض كل ثانية،
// وبالثانيتين الأخيرات بيتحول للون التحذير.
export const Countdown: React.FC<{ theme: Theme; seconds: number; size?: number }> = ({
  theme,
  seconds,
  size = 230,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = seconds * fps;
  const progress = Math.min(frame / total, 1);
  const remaining = Math.max(Math.ceil(seconds - frame / fps), 0);
  const inSecond = (frame % fps) / fps;
  const urgent = remaining <= 2;
  const stroke = 18;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const color = urgent ? theme.accent : theme.primary;

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ rotate: "-90deg" }}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke={theme.muted} strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * progress}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONT_UI,
          fontWeight: 900,
          fontSize: size * 0.46,
          color,
          scale: String(interpolate(inSecond, [0, 0.15, 0.5], [1.25, 1, 1], { extrapolateRight: "clamp" })),
        }}
      >
        {remaining}
      </div>
    </div>
  );
};
