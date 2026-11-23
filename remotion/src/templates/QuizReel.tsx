import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  type CalculateMetadataFunction,
  Easing,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { Background } from "../components/Background";
import { Captions } from "../components/Captions";
import { Countdown } from "../components/Countdown";
import { Logo } from "../components/Logo";
import { SafeArea } from "../components/SafeArea";
import { CheckIcon, Sfx } from "../components/ui";
import { getMediaDuration, resolveSrc, sec } from "../lib/media";
import { FONT_UI } from "../theme/fonts";
import { getTheme, type Theme, zChannel } from "../theme/themes";

// قالب كويز: لوغو ← سؤال و4 خيارات (1 2 3 4) ← مؤقت ← كشف الجواب ← التحليل ← دعوة للتعليق.
// كل الأوقات بالثواني. إذا حطيت صوت للسؤال أو للجواب، المشهد بيطول لحاله على قد الصوت.

export const quizSchema = z.object({
  channel: zChannel,
  logo: z.string().optional().describe("مسار صورة اللوغو داخل public، مثل brand/quizzawi.png"),
  introSfx: z.string().describe("صوت ظهور اللوغو (نفس صوت المقدمة بكل الفيديوهات)"),
  category: z.string(),
  question: z.string(),
  options: z.tuple([z.string(), z.string(), z.string(), z.string()]),
  correct: z.number().int().min(1).max(4),
  explanation: z.string(),
  cta: z.string(),
  thinkSeconds: z.number().min(2).max(15),
  voiceQuestion: z.string().optional().describe("صوت السؤال والخيارات"),
  voiceAnswer: z.string().optional().describe("صوت الجواب والتحليل"),
  captionsQuestion: z.string().optional(),
  captionsAnswer: z.string().optional(),
  backgroundImage: z.string().optional(),
  music: z.string().optional(),
  musicVolume: z.number().min(0).max(1),
  timing: z.object({
    intro: z.number(),
    question: z.number(),
    reveal: z.number(),
    explanation: z.number(),
    outro: z.number(),
  }),
  showSafeArea: z.boolean(),
});

export type QuizProps = z.infer<typeof quizSchema>;

const FPS = 30;

const scenes = (p: QuizProps) => {
  const t = p.timing;
  const intro = 0;
  const question = intro + t.intro;
  const think = question + t.question;
  const reveal = think + p.thinkSeconds;
  const explanation = reveal + t.reveal;
  const outro = explanation + t.explanation;
  const end = outro + t.outro;
  return { intro, question, think, reveal, explanation, outro, end };
};

export const calculateQuizMetadata: CalculateMetadataFunction<QuizProps> = async ({ props }) => {
  const timing = { ...props.timing };
  if (props.voiceQuestion) {
    timing.question = Math.max(timing.question, (await getMediaDuration(props.voiceQuestion)) + 0.4);
  }
  if (props.voiceAnswer) {
    const need = (await getMediaDuration(props.voiceAnswer)) + 0.4 - timing.reveal;
    timing.explanation = Math.max(timing.explanation, need);
  }
  const next = { ...props, timing };
  return { durationInFrames: sec(scenes(next).end, FPS), fps: FPS, props: next };
};

export const QuizReel: React.FC<QuizProps> = (p) => {
  const theme = getTheme(p.channel);
  const { fps } = useVideoConfig();
  const s = scenes(p);
  const f = (x: number) => sec(x, fps);

  return (
    <AbsoluteFill style={{ direction: "rtl", fontFamily: FONT_UI }}>
      <Background theme={theme} image={p.backgroundImage} />

      {/* 1) مقدمة: اللوغو بالنص مع صوت المقدمة */}
      <Sequence name="Intro" from={f(s.intro)} durationInFrames={f(p.timing.intro)}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <Logo theme={theme} src={p.logo} size={560} />
        </AbsoluteFill>
      </Sequence>
      <Sfx src={p.introSfx} at={s.intro} />

      {/* 2) السؤال والخيارات والمؤقت وكشف الجواب */}
      <Sequence name="Question" from={f(s.question)} durationInFrames={f(s.explanation - s.question)}>
        <QuestionScene
          p={p}
          theme={theme}
          thinkFrom={f(s.think - s.question)}
          revealFrom={f(s.reveal - s.question)}
        />
      </Sequence>
      {p.options.map((_, i) => (
        <Sfx key={i} src="sfx/whoosh-short.wav" at={s.question + 0.5 + i * 0.25} volume={0.35} />
      ))}
      {Array.from({ length: p.thinkSeconds }, (_, i) => (
        <Sfx key={`tick${i}`} src="sfx/tick.wav" at={s.think + i} volume={0.9} />
      ))}
      <Sfx src="sfx/timer-end.wav" at={s.reveal - 0.2} volume={0.6} />
      <Sfx src="sfx/correct.wav" at={s.reveal + 0.1} volume={0.7} />

      {/* 3) التحليل */}
      <Sequence name="Explanation" from={f(s.explanation)} durationInFrames={f(p.timing.explanation)}>
        <ExplanationScene p={p} theme={theme} />
      </Sequence>

      {/* 4) دعوة للتعليق */}
      <Sequence name="Outro" from={f(s.outro)} durationInFrames={f(p.timing.outro)}>
        <OutroScene p={p} theme={theme} />
      </Sequence>

      {/* الأصوات */}
      {p.voiceQuestion ? (
        <Sequence name="Voice question" from={f(s.question)} layout="none">
          <Audio src={resolveSrc(p.voiceQuestion)} />
        </Sequence>
      ) : null}
      {p.voiceAnswer ? (
        <Sequence name="Voice answer" from={f(s.reveal)} layout="none">
          <Audio src={resolveSrc(p.voiceAnswer)} />
        </Sequence>
      ) : null}
      {p.captionsQuestion ? (
        <Sequence from={f(s.question)} durationInFrames={f(s.think - s.question)}>
          <Captions theme={theme} src={p.captionsQuestion} bottom={1920 - 1500} />
        </Sequence>
      ) : null}
      {p.captionsAnswer ? (
        <Sequence from={f(s.reveal)} durationInFrames={f(s.end - s.reveal)}>
          <Captions theme={theme} src={p.captionsAnswer} />
        </Sequence>
      ) : null}
      {p.music ? <Audio src={resolveSrc(p.music)} volume={p.musicVolume} loop /> : null}

      {p.showSafeArea ? <SafeArea /> : null}
    </AbsoluteFill>
  );
};

const Header: React.FC<{ p: QuizProps; theme: Theme }> = ({ p, theme }) => (
  <div style={{ position: "absolute", top: 230, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
    <Logo theme={theme} src={p.logo} size={150} pop={false} />
    <div
      style={{
        background: theme.accent,
        color: theme.cardText,
        fontWeight: 800,
        fontSize: 36,
        padding: "6px 30px",
        borderRadius: 999,
      }}
    >
      {p.category}
    </div>
  </div>
);

const QuestionScene: React.FC<{ p: QuizProps; theme: Theme; thinkFrom: number; revealFrom: number }> = ({
  p,
  theme,
  thinkFrom,
  revealFrom,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 120 } });
  const revealed = frame >= revealFrom;

  return (
    <AbsoluteFill>
      <Header p={p} theme={theme} />

      {/* كرت السؤال */}
      <div
        style={{
          position: "absolute",
          top: 470,
          left: 90,
          right: 90,
          minHeight: 250,
          background: theme.card,
          color: theme.cardText,
          borderRadius: 40,
          padding: "36px 44px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          fontWeight: 800,
          fontSize: p.question.length > 70 ? 52 : 60,
          lineHeight: 1.4,
          boxShadow: `0 14px 0 ${theme.accent}, 0 30px 60px rgba(0,0,0,0.35)`,
          opacity: enter,
          translate: `0px ${interpolate(enter, [0, 1], [-60, 0])}px`,
        }}
      >
        {p.question}
      </div>

      {/* الخيارات */}
      <div style={{ position: "absolute", top: 800, left: 90, right: 90, display: "flex", flexDirection: "column", gap: 26 }}>
        {p.options.map((option, i) => (
          <OptionBar
            key={i}
            n={i + 1}
            text={option}
            theme={theme}
            appearAt={Math.round((0.5 + i * 0.25) * fps)}
            state={!revealed ? "idle" : i + 1 === p.correct ? "correct" : "dim"}
            revealAt={revealFrom}
          />
        ))}
      </div>

      {/* المؤقت */}
      <Sequence from={thinkFrom} durationInFrames={revealFrom - thinkFrom + Math.round(0.4 * fps)} layout="none">
        <TimerSlot theme={theme} seconds={p.thinkSeconds} />
      </Sequence>
    </AbsoluteFill>
  );
};

const TimerSlot: React.FC<{ theme: Theme; seconds: number }> = ({ theme, seconds }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const end = seconds * fps;
  return (
    <div
      style={{
        position: "absolute",
        top: 1330,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity: interpolate(frame, [0, 6, end, end + 10], [0, 1, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
        scale: String(interpolate(frame, [0, 8], [0.6, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.back(2)) })),
      }}
    >
      <Countdown theme={theme} seconds={seconds} size={170} />
    </div>
  );
};

const OptionBar: React.FC<{
  n: number;
  text: string;
  theme: Theme;
  appearAt: number;
  state: "idle" | "correct" | "dim";
  revealAt: number;
}> = ({ n, text, theme, appearAt, state, revealAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - appearAt, fps, config: { damping: 14, stiffness: 160 } });
  const pop = spring({ frame: frame - revealAt, fps, config: { damping: 8, stiffness: 180 } });
  const correct = state === "correct";

  return (
    <div
      style={{
        height: 118,
        borderRadius: 30,
        display: "flex",
        alignItems: "center",
        gap: 24,
        padding: "0 22px",
        background: correct ? theme.correct : theme.card,
        color: correct ? "#FFFFFF" : theme.cardText,
        fontWeight: 800,
        fontSize: text.length > 26 ? 40 : 46,
        opacity: state === "dim" ? 0.4 : enter,
        translate: `${interpolate(enter, [0, 1], [140, 0])}px 0px`,
        scale: correct ? String(interpolate(pop, [0, 1], [1, 1.05])) : "1",
        boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
      }}
    >
      <div
        style={{
          width: 82,
          height: 82,
          flexShrink: 0,
          borderRadius: 999,
          background: correct ? "#FFFFFF" : theme.accent,
          color: correct ? theme.correct : theme.cardText,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 900,
          fontSize: 50,
        }}
      >
        {n}
      </div>
      <div style={{ flex: 1, lineHeight: 1.25 }}>{text}</div>
      {correct ? <CheckIcon size={64} color="#FFFFFF" /> : null}
    </div>
  );
};

const ExplanationScene: React.FC<{ p: QuizProps; theme: Theme }> = ({ p, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 15, stiffness: 120 } });
  return (
    <AbsoluteFill>
      <Header p={p} theme={theme} />
      <div
        style={{
          position: "absolute",
          top: 520,
          left: 90,
          right: 90,
          display: "flex",
          flexDirection: "column",
          gap: 30,
          alignItems: "center",
          opacity: enter,
          translate: `0px ${interpolate(enter, [0, 1], [50, 0])}px`,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            background: theme.correct,
            color: "#FFFFFF",
            borderRadius: 999,
            padding: "14px 40px",
            fontWeight: 900,
            fontSize: 50,
          }}
        >
          <CheckIcon size={54} color="#FFFFFF" />
          الجواب {p.correct}: {p.options[p.correct - 1]}
        </div>
        <div
          style={{
            background: theme.card,
            color: theme.cardText,
            borderRadius: 40,
            padding: "40px 46px",
            fontWeight: 700,
            fontSize: p.explanation.length > 160 ? 44 : 50,
            lineHeight: 1.55,
            textAlign: "center",
            boxShadow: `0 14px 0 ${theme.accent}`,
          }}
        >
          {p.explanation}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const OutroScene: React.FC<{ p: QuizProps; theme: Theme }> = ({ p, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 10, stiffness: 140 } });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 50 }}>
      <Logo theme={theme} src={p.logo} size={380} />
      <div
        style={{
          maxWidth: 860,
          textAlign: "center",
          color: theme.text,
          fontWeight: 900,
          fontSize: 66,
          lineHeight: 1.4,
          scale: String(enter),
        }}
      >
        {p.cta}
      </div>
    </AbsoluteFill>
  );
};
