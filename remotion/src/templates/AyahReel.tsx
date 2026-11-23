import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  type CalculateMetadataFunction,
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
import { getMediaDuration, resolveSrc, sec } from "../lib/media";
import { getAyat, recitationPath, toArabicDigits } from "../lib/quran";
import { FONT_QURAN, FONT_UI } from "../theme/fonts";
import { getTheme, type Theme, zChannel } from "../theme/themes";

// قالب «ثمرة آية»: عنوان ← الآيات بالتلاوة (النص من تنزيل) ← الثمرات ← خاتمة.
// بدون موسيقى. اكتب رقم السورة والآيات بس، والنص بينسحب تلقائياً.

export const ayahSchema = z.object({
  channel: zChannel,
  logo: z.string().optional(),
  title: z.string(),
  episode: z.number().int().optional(),
  sura: z.number().int().min(1).max(114),
  ayaFrom: z.number().int().min(1),
  ayaTo: z.number().int().min(1),
  reciter: z.string().describe("اسم مجلد القارئ، مثل Yasser_Ad-Dussary_128kbps أو MaherAlMuaiqly128kbps"),
  audioBase: z.string().describe("مكان ملفات التلاوة: رابط مستودع thamarat-aya-audio أو مجلد داخل public"),
  lessonsTitle: z.string(),
  lessons: z.array(z.string()).min(1).max(4).describe("الثمرات — راجعها مع مختص قبل النشر"),
  voiceLessons: z.string().optional(),
  captionsLessons: z.string().optional(),
  cta: z.string(),
  backgroundImage: z.string().optional(),
  timing: z.object({ intro: z.number(), gap: z.number(), perLesson: z.number(), outro: z.number() }),
  showSafeArea: z.boolean(),
  resolved: z
    .object({
      suraName: z.string(),
      basmalaText: z.string(),
      ayat: z.array(
        z.object({ aya: z.number(), text: z.string(), basmala: z.boolean(), audio: z.string(), duration: z.number() }),
      ),
    })
    .optional()
    .describe("بيتعبى تلقائياً من تنزيل وملفات التلاوة — لا تعدّله"),
});

export type AyahProps = z.infer<typeof ayahSchema>;
type Resolved = NonNullable<AyahProps["resolved"]>;

const FPS = 30;

const layout = (p: AyahProps, r: Resolved) => {
  const ayatStart = p.timing.intro;
  const ayat = r.ayat.map((a, i) => {
    const start = ayatStart + r.ayat.slice(0, i).reduce((s, x) => s + x.duration + p.timing.gap, 0);
    return { ...a, start, length: a.duration + p.timing.gap };
  });
  const lessonsStart = ayat.length ? ayat[ayat.length - 1].start + ayat[ayat.length - 1].length : ayatStart;
  const lessonsLength = p.lessons.length * p.timing.perLesson;
  const outro = lessonsStart + lessonsLength;
  return { ayat, lessonsStart, lessonsLength, outro, end: outro + p.timing.outro };
};

export const calculateAyahMetadata: CalculateMetadataFunction<AyahProps> = async ({ props }) => {
  const { sura, ayat, basmalaText } = await getAyat(props.sura, props.ayaFrom, props.ayaTo);
  const withAudio = await Promise.all(
    ayat.map(async (a) => {
      const audio = recitationPath(props.audioBase, props.reciter, a.sura, a.aya);
      let duration: number;
      try {
        duration = await getMediaDuration(audio);
      } catch {
        throw new Error(
          `ما لقيت تلاوة ${a.sura}:${a.aya} (${audio}). ضيف الآية لملف verses.txt بمستودع thamarat-aya-audio وخلّي الـAction ينزّلها.`,
        );
      }
      return { aya: a.aya, text: a.text, basmala: a.basmala, audio, duration };
    }),
  );
  const resolved: Resolved = { suraName: sura.name, basmalaText, ayat: withAudio };
  const timing = { ...props.timing };
  if (props.voiceLessons) {
    const voice = await getMediaDuration(props.voiceLessons);
    timing.perLesson = Math.max(timing.perLesson, (voice + 0.5) / props.lessons.length);
  }
  const next = { ...props, timing, resolved };
  return { durationInFrames: sec(layout(next, resolved).end, FPS), fps: FPS, props: next };
};

export const AyahReel: React.FC<AyahProps> = (p) => {
  const theme = getTheme(p.channel);
  const { fps } = useVideoConfig();
  if (!p.resolved) return null;
  const r = p.resolved;
  const L = layout(p, r);
  const f = (x: number) => sec(x, fps);
  const range =
    p.ayaFrom === p.ayaTo ? `الآية ${p.ayaFrom}` : `الآيات ${p.ayaFrom}–${p.ayaTo}`;

  return (
    <AbsoluteFill style={{ direction: "rtl", fontFamily: FONT_UI }}>
      <Background theme={theme} image={p.backgroundImage} imageOpacity={0.3} />

      <Sequence name="Intro"  durationInFrames={f(p.timing.intro)}>
        <IntroScene p={p} theme={theme} subtitle={`سورة ${r.suraName} · ${range}`} />
      </Sequence>

      {L.ayat.map((a) => (
        <Sequence key={a.aya} name={`Ayah ${a.aya}`} from={f(a.start)} durationInFrames={f(a.length)}>
          <AyahScene theme={theme} text={a.text} aya={a.aya} basmala={a.basmala ? r.basmalaText : null} suraName={r.suraName} />
          <Audio src={resolveSrc(a.audio)} />
        </Sequence>
      ))}

      <Sequence name="Lessons" from={f(L.lessonsStart)} durationInFrames={f(L.lessonsLength)}>
        <LessonsScene p={p} theme={theme} />
        {p.voiceLessons ? <Audio src={resolveSrc(p.voiceLessons)} /> : null}
        {p.captionsLessons ? <Captions theme={theme} src={p.captionsLessons} /> : null}
      </Sequence>

      <Sequence name="Outro" from={f(L.outro)} durationInFrames={f(p.timing.outro)}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 40 }}>
          <Logo theme={theme} src={p.logo} size={360} />
          <div style={{ color: theme.text, fontWeight: 800, fontSize: 58, textAlign: "center", maxWidth: 860, lineHeight: 1.4 }}>
            {p.cta}
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* نسبة النص لمشروع تنزيل (شرط من شروط استخدامه) */}
      <TanzilCredit theme={theme} from={f(p.timing.intro)} to={f(L.lessonsStart)} />

      {p.showSafeArea ? <SafeArea /> : null}
    </AbsoluteFill>
  );
};

const IntroScene: React.FC<{ p: AyahProps; theme: Theme; subtitle: string }> = ({ p, theme, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - 8, fps, config: { damping: 14 } });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 36 }}>
      <Logo theme={theme} src={p.logo} size={420} />
      {p.episode ? (
        <div style={{ color: theme.accent, fontWeight: 700, fontSize: 40, opacity: enter }}>الحلقة {p.episode}</div>
      ) : null}
      <div
        style={{
          color: theme.text,
          fontWeight: 800,
          fontSize: 54,
          opacity: enter,
          translate: `0px ${interpolate(enter, [0, 1], [30, 0])}px`,
        }}
      >
        {subtitle}
      </div>
    </AbsoluteFill>
  );
};

const ayahFontSize = (len: number) => (len <= 60 ? 88 : len <= 120 ? 76 : len <= 200 ? 64 : len <= 320 ? 56 : len <= 450 ? 48 : 42);

const AyahScene: React.FC<{ theme: Theme; text: string; aya: number; basmala: string | null; suraName: string }> = ({
  theme,
  text,
  aya,
  basmala,
  suraName,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 90 } });
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        paddingTop: SAFE.top,
        paddingBottom: SAFE.bottom + 60,
        paddingLeft: SAFE.side,
        paddingRight: SAFE.right,
      }}
    >
      <div style={{ color: theme.accent, fontWeight: 700, fontSize: 38, marginBottom: 30, opacity: enter }}>
        سورة {suraName}
      </div>
      {basmala ? (
        <div style={{ fontFamily: FONT_QURAN, color: theme.primary, fontSize: 54, marginBottom: 24, opacity: enter }}>
          {basmala}
        </div>
      ) : null}
      <div
        style={{
          fontFamily: FONT_QURAN,
          color: theme.text,
          fontSize: ayahFontSize(text.length),
          lineHeight: 2.05,
          textAlign: "center",
          opacity: enter,
          scale: String(interpolate(enter, [0, 1], [0.96, 1])),
        }}
      >
        <span style={{ color: theme.primary }}>﴿</span>
        {text}
        <span style={{ color: theme.primary, whiteSpace: "nowrap" }}> {"۝"}{toArabicDigits(aya)}﴾</span>
      </div>
    </AbsoluteFill>
  );
};

const LessonsScene: React.FC<{ p: AyahProps; theme: Theme }> = ({ p, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const per = p.timing.perLesson * fps;
  return (
    <AbsoluteFill style={{ paddingTop: SAFE.top + 40, alignItems: "center" }}>
      <div style={{ color: theme.primary, fontWeight: 900, fontSize: 72, marginBottom: 46 }}>{p.lessonsTitle}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 30, width: 1080 - SAFE.side - SAFE.right }}>
        {p.lessons.map((lesson, i) => {
          const s = spring({ frame: frame - i * per, fps, config: { damping: 15 } });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                gap: 24,
                alignItems: "center",
                background: theme.card,
                color: theme.cardText,
                borderRadius: 32,
                padding: "28px 32px",
                fontWeight: 700,
                fontSize: lesson.length > 80 ? 40 : 46,
                lineHeight: 1.5,
                opacity: s,
                translate: `${interpolate(s, [0, 1], [120, 0])}px 0px`,
              }}
            >
              <div
                style={{
                  flexShrink: 0,
                  width: 72,
                  height: 72,
                  borderRadius: 999,
                  background: theme.primary,
                  color: theme.cardText,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 900,
                  fontSize: 42,
                }}
              >
                {i + 1}
              </div>
              <div>{lesson}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const TanzilCredit: React.FC<{ theme: Theme; from: number; to: number }> = ({ theme, from, to }) => (
  <Sequence from={from} durationInFrames={Math.max(to - from, 1)} layout="none">
    <div
      style={{
        position: "absolute",
        bottom: SAFE.bottom + 6,
        left: 0,
        right: 0,
        textAlign: "center",
        color: theme.muted,
        fontSize: 26,
        fontWeight: 600,
      }}
    >
      النص القرآني من مشروع تنزيل · tanzil.net
    </div>
  </Sequence>
);
