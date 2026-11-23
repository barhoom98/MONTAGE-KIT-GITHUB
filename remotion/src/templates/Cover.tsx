import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { Background } from "../components/Background";
import { Logo } from "../components/Logo";
import { FONT_UI } from "../theme/fonts";
import { getTheme, zChannel } from "../theme/themes";

// غلاف الريل (صورة ثابتة 1080×1920). العنوان بالنص عشان ما ينقص
// لما إنستغرام يقص الغلاف بشبكة البروفايل (3:4).

export const coverSchema = z.object({
  channel: zChannel,
  logo: z.string().optional(),
  badge: z.string().optional().describe("شارة صغيرة فوق العنوان، مثل: سؤال اليوم #24"),
  title: z.string(),
  subtitle: z.string().optional(),
  image: z.string().optional(),
});

export type CoverProps = z.infer<typeof coverSchema>;

export const Cover: React.FC<CoverProps> = (p) => {
  const theme = getTheme(p.channel);
  return (
    <AbsoluteFill style={{ direction: "rtl", fontFamily: FONT_UI }}>
      <Background theme={theme} image={p.image} imageOpacity={0.55} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 40, padding: "0 90px" }}>
        <Logo theme={theme} src={p.logo} size={220} pop={false} />
        {p.badge ? (
          <div
            style={{
              background: theme.accent,
              color: theme.cardText,
              fontWeight: 800,
              fontSize: 48,
              padding: "8px 40px",
              borderRadius: 999,
            }}
          >
            {p.badge}
          </div>
        ) : null}
        <div
          style={{
            color: theme.primary,
            fontWeight: 900,
            fontSize: p.title.length > 30 ? 104 : 124,
            lineHeight: 1.25,
            textAlign: "center",
            WebkitTextStroke: `14px ${theme.bgBottom}`,
            paintOrder: "stroke fill",
            textShadow: "0 12px 40px rgba(0,0,0,0.5)",
          }}
        >
          {p.title}
        </div>
        {p.subtitle ? (
          <div style={{ color: theme.text, fontWeight: 700, fontSize: 52, textAlign: "center", lineHeight: 1.4 }}>
            {p.subtitle}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
