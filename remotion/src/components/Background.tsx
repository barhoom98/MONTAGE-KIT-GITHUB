import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { resolveSrc } from "../lib/media";
import type { Theme } from "../theme/themes";

// خلفية القناة: تدرج بألوانها + صورة اختيارية بحركة تكبير بطيئة (Ken Burns)
export const Background: React.FC<{
  theme: Theme;
  image?: string;
  imageOpacity?: number;
}> = ({ theme, image, imageOpacity = 0.45 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${theme.bgTop} 0%, ${theme.bgBottom} 100%)`,
      }}
    >
      {image ? (
        <AbsoluteFill style={{ opacity: imageOpacity }}>
          <Img
            src={resolveSrc(image)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              scale: interpolate(frame, [0, durationInFrames], [1, 1.12], {
                extrapolateRight: "clamp",
              }),
            }}
          />
        </AbsoluteFill>
      ) : null}
      {/* توهج خفيف بلون القناة */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 30%, ${theme.primary}33 0%, transparent 55%)`,
        }}
      />
      {/* تعتيم تحت عشان النص يضل مقروء */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, transparent 40%, ${theme.bgBottom}CC 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};
