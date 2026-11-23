import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  type CalculateMetadataFunction,
  Img,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { Background } from "../components/Background";
import { Captions } from "../components/Captions";
import { Logo } from "../components/Logo";
import { SAFE, SafeArea } from "../components/SafeArea";
import { Sfx } from "../components/ui";
import { getMediaDuration, resolveSrc, sec } from "../lib/media";
import { FONT_UI } from "../theme/fonts";
import { getTheme, type Theme, zChannel } from "../theme/themes";

// قالب نصائح عام (تغذية، محاسبة، جيم): هوك ← نقاط مرقّمة بصور ← دعوة للمتابعة.
// إذا حطيت تعليق صوتي، وقت النقاط بيتمدد لحاله على قد الصوت.

export const tipSchema = z.object({
  channel: zChannel,
  logo: z.string().optional(),
  hook: z.string().describe("أول جملة على الشاشة (أول ثانيتين)"),
  title: z.string(),
  points: z
    .array(z.object({ title: z.string(), body: z.string(), image: z.string().optional() }))
    .min(1)
    .max(6),
  cta: z.string(),
  voiceover: z.string().optional(),
  captions: z.string().optional(),
  backgroundImage: z.string().optional(),
  music: z.string().optional(),
  musicVolume: z.number().min(0).max(1),
  timing: z.object({ hook: z.number(), perPoint: z.number(), cta: z.number() }),
  showSafeArea: z.boolean(),
});

export type TipProps = z.infer<typeof tipSchema>;

const FPS = 30;

export const calculateTipMetadata: CalculateMetadataFunction<TipProps> = async ({ props }) => {
  const timing = { ...props.timing };
  const base = () => timing.hook + props.points.length * timing.perPoint + timing.cta;
  if (props.voiceover) {
    const voice = await getMediaDuration(props.voiceover);
    if (voice + 0.5 > base()) timing.perPoint += (voice + 0.5 - base()) / props.points.length;
  }
  const next = { ...props, timing };
  return { durationInFrames: sec(base(), FPS), fps: FPS, props: next };
};

export const TipReel: React.FC<TipProps> = (p) => {
  const theme = getTheme(p.channel);
  const { fps } = useVideoConfig();
  const f = (x: number) => sec(x, fps);
  const pointsStart = p.timing.hook;
  const ctaStart = pointsStart + p.points.length * p.timing.perPoint;

  return (
    <AbsoluteFill style={{ direction: "rtl", fontFamily: FONT_UI }}>
      <Background theme={theme} image={p.backgroundImage} />

      <Sequence name="Hook"  durationInFrames={f(p.timing.hook)}>
        <HookScene p={p} theme={theme} />
      </Sequence>
      <Sfx src="sfx/pop-modern.wav" at={0.05} volume={0.6} />

      {p.points.map((point, i) => (
        <Sequence key={i} name={`Point ${i + 1}`} from={f(pointsStart + i * p.timing.perPoint)} durationInFrames={f(p.timing.perPoint)}>
          <PointScene theme={theme} n={i + 1} total={p.points.length} point={point} />
        </Sequence>
      ))}
      {p.points.map((_, i) => (
        <Sfx key={`s${i}`} src="sfx/whoosh-short.wav" at={pointsStart + i * p.timing.perPoint} volume={0.4} />
      ))}

      <Sequence name="CTA" from={f(ctaStart)} durationInFrames={f(p.timing.cta)}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 44 }}>
          <Logo theme={theme} src={p.logo} size={360} />
          <div style={{ color: theme.text, fontWeight: 900, fontSize: 64, textAlign: "center", maxWidth: 860, lineHeight: 1.4 }}>
            {p.cta}
          </div>
        </AbsoluteFill>
      </Sequence>

      {p.voiceover ? <Audio src={resolveSrc(p.voiceover)} /> : null}
      {p.captions ? <Captions theme={theme} src={p.captions} /> : null}
      {p.music ? <Audio src={resolveSrc(p.music)} volume={p.musicVolume} loop /> : null}
      {p.showSafeArea ? <SafeArea /> : null}
    </AbsoluteFill>
  );
};

const HookScene: React.FC<{ p: TipProps; theme: Theme }> = ({ p, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 9, stiffness: 160 } });
  const sub = spring({ frame: frame - 10, fps, config: { damping: 14 } });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 40, padding: `0 ${SAFE.right}px 0 ${SAFE.side}px` }}>
      <div
        style={{
          background: theme.primary,
          color: theme.cardText,
          fontWeight: 800,
          fontSize: 40,
          padding: "8px 34px",
          borderRadius: 999,
          opacity: sub,
        }}
      >
        {p.title}
      </div>
      <div
        style={{
          color: theme.text,
          fontWeight: 900,
          fontSize: p.hook.length > 40 ? 84 : 100,
          lineHeight: 1.3,
          textAlign: "center",
          scale: String(pop),
          textShadow: "0 8px 30px rgba(0,0,0,0.45)",
        }}
      >
        {p.hook}
      </div>
    </AbsoluteFill>
  );
};

const PointScene: React.FC<{ theme: Theme; n: number; total: number; point: TipProps["points"][number] }> = ({
  theme,
  n,
  total,
  point,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 15, stiffness: 130 } });
  const text = spring({ frame: frame - 6, fps, config: { damping: 16 } });

  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: point.image ? "flex-start" : "center",
        paddingTop: SAFE.top + 70,
        paddingBottom: SAFE.bottom,
      }}
    >
      {/* شريط التقدم */}
      <div style={{ position: "absolute", top: SAFE.top, display: "flex", gap: 12 }}>
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            style={{
              width: i + 1 === n ? 64 : 22,
              height: 22,
              borderRadius: 999,
              background: i + 1 <= n ? theme.primary : theme.muted,
            }}
          />
        ))}
      </div>

      {point.image ? (
        <div
          style={{
            width: 1080 - SAFE.side - SAFE.right,
            height: 560,
            borderRadius: 44,
            overflow: "hidden",
            boxShadow: `0 16px 0 ${theme.accent}, 0 30px 60px rgba(0,0,0,0.4)`,
            opacity: enter,
            scale: String(interpolate(enter, [0, 1], [0.9, 1])),
          }}
        >
          <Img
            src={resolveSrc(point.image)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              scale: String(interpolate(frame, [0, durationInFrames], [1.05, 1.18])),
            }}
          />
        </div>
      ) : null}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 26,
          marginTop: point.image ? 56 : 0,
          width: 1080 - SAFE.side - SAFE.right,
          opacity: text,
          translate: `${interpolate(text, [0, 1], [80, 0])}px 0px`,
        }}
      >
        <div
          style={{
            flexShrink: 0,
            width: 110,
            height: 110,
            borderRadius: 32,
            background: theme.accent,
            color: theme.cardText,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 900,
            fontSize: 70,
            rotate: "-4deg",
          }}
        >
          {n}
        </div>
        <div style={{ color: theme.primary, fontWeight: 900, fontSize: (point.title.length > 22 ? 60 : 72) + (point.image ? 0 : 12), lineHeight: 1.25 }}>
          {point.title}
        </div>
      </div>
      <div
        style={{
          marginTop: 26,
          width: 1080 - SAFE.side - SAFE.right,
          color: theme.text,
          fontWeight: 700,
          fontSize: (point.body.length > 90 ? 42 : 48) + (point.image ? 0 : 6),
          lineHeight: 1.5,
          opacity: text,
        }}
      >
        {point.body}
      </div>
    </AbsoluteFill>
  );
};
