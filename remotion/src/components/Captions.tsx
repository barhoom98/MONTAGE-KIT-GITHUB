import type { Caption, TikTokPage } from "@remotion/captions";
import { createTikTokStyleCaptions } from "@remotion/captions";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AbsoluteFill, Sequence, spring, useCurrentFrame, useDelayRender, useVideoConfig } from "remotion";
import { resolveSrc } from "../lib/media";
import { FONT_UI } from "../theme/fonts";
import type { Theme } from "../theme/themes";
import { SAFE } from "./SafeArea";

// ترجمة عربية كلمة بكلمة. الملف JSON بصيغة Caption تبعت Remotion،
// وبيطلع من سكربت scripts/elevenlabs-captions.mjs.
const SWITCH_EVERY_MS = 1100;

export const Captions: React.FC<{ theme: Theme; src: string; bottom?: number }> = ({
  theme,
  src,
  bottom = SAFE.bottom + 40,
}) => {
  const [captions, setCaptions] = useState<Caption[] | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender(`captions ${src}`));
  const { fps } = useVideoConfig();

  const load = useCallback(async () => {
    try {
      const res = await fetch(resolveSrc(src));
      setCaptions((await res.json()) as Caption[]);
      continueRender(handle);
    } catch (e) {
      cancelRender(e);
    }
  }, [src, continueRender, cancelRender, handle]);

  useEffect(() => {
    load();
  }, [load]);

  const pages = useMemo(
    () =>
      captions
        ? createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: SWITCH_EVERY_MS }).pages
        : [],
    [captions],
  );

  return (
    <AbsoluteFill>
      {pages.map((page, i) => {
        const next = pages[i + 1];
        const from = Math.round((page.startMs / 1000) * fps);
        const end = Math.min(
          next ? Math.round((next.startMs / 1000) * fps) : Infinity,
          from + Math.round(((page.durationMs + 400) / 1000) * fps),
        );
        if (end - from <= 0) return null;
        return (
          <Sequence key={i} from={from} durationInFrames={end - from} layout="none">
            <CaptionPage theme={theme} page={page} bottom={bottom} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const CaptionPage: React.FC<{ theme: Theme; page: TikTokPage; bottom: number }> = ({ theme, page, bottom }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = page.startMs + (frame / fps) * 1000;
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 200 } });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: bottom }}>
      <div
        style={{
          direction: "rtl",
          maxWidth: 1080 - 2 * SAFE.right,
          textAlign: "center",
          fontFamily: FONT_UI,
          fontWeight: 900,
          fontSize: 76,
          lineHeight: 1.35,
          whiteSpace: "pre-wrap",
          color: theme.text,
          WebkitTextStroke: `10px ${theme.bgBottom}`,
          paintOrder: "stroke fill",
          scale: String(0.85 + 0.15 * enter),
        }}
      >
        {page.tokens.map((token, i) => {
          const active = token.fromMs <= t && token.toMs > t;
          return (
            <span key={`${token.fromMs}-${i}`} style={{ color: active ? theme.primary : theme.text }}>
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
