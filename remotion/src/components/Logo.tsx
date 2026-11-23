import { Img, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { resolveSrc } from "../lib/media";
import { FONT_UI } from "../theme/fonts";
import type { Theme } from "../theme/themes";

// لوغو القناة بحركة ظهور (pop-in). إذا ما في صورة لوغو بيطلع اسم القناة مكتوب.
export const Logo: React.FC<{
  theme: Theme;
  src?: string;
  size: number;
  pop?: boolean;
}> = ({ theme, src, size, pop = true }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = pop ? spring({ frame, fps, config: { damping: 9, stiffness: 140, mass: 0.8 } }) : 1;

  if (src) {
    return (
      <Img
        src={resolveSrc(src)}
        style={{ width: size, height: size, objectFit: "contain", scale: String(s) }}
      />
    );
  }

  return (
    <div
      style={{
        scale: String(s),
        fontFamily: FONT_UI,
        fontWeight: 900,
        fontSize: size * 0.32,
        color: theme.primary,
        textShadow: `0 ${size * 0.03}px 0 ${theme.accent}, 0 ${size * 0.06}px ${size * 0.12}px rgba(0,0,0,0.45)`,
        whiteSpace: "nowrap",
      }}
    >
      {theme.name}
    </div>
  );
};
