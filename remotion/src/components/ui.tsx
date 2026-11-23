import { Audio } from "@remotion/media";
import { Sequence, useVideoConfig } from "remotion";
import { resolveSrc } from "../lib/media";

// مؤثر صوتي بيبلش عند ثانية معينة
export const Sfx: React.FC<{ src: string; at: number; volume?: number }> = ({ src, at, volume = 0.8 }) => {
  const { fps } = useVideoConfig();
  return (
    <Sequence from={Math.round(at * fps)} layout="none" name={`sfx ${src}`}>
      <Audio src={resolveSrc(src)} volume={volume} />
    </Sequence>
  );
};

// علامة صح كـ SVG (ما بنعتمد على وجودها بالخط)
export const CheckIcon: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M4 12.5l5 5L20 6.5" stroke={color} strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);
