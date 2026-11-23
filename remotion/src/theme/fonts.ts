import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// خطوط محلية (مرخصة OFL، مسموح استخدامها تجارياً). ملفات الترخيص بـ public/fonts.
// Cairo للعناوين والنصوص، وAmiri Quran لنص الآيات بالرسم العثماني.
// كل خط إله ملفين: عربي ولاتيني (للأرقام 1 2 3 4 والحروف الإنجليزية).

const CAIRO_WEIGHTS = ["400", "600", "700", "800", "900"] as const;

export const FONT_UI = '"Cairo", "CairoLatin", sans-serif';
export const FONT_QURAN = '"AmiriQuran", "AmiriQuranLatin", "Cairo", serif';

export const fontsReady = Promise.all([
  ...CAIRO_WEIGHTS.flatMap((weight) => [
    loadFont({
      family: "Cairo",
      url: staticFile(`fonts/cairo-arabic-${weight}-normal.woff2`),
      weight,
    }),
    loadFont({
      family: "CairoLatin",
      url: staticFile(`fonts/cairo-latin-${weight}-normal.woff2`),
      weight,
    }),
  ]),
  loadFont({
    family: "AmiriQuran",
    url: staticFile("fonts/amiri-quran-arabic-400-normal.woff2"),
    weight: "400",
  }),
  loadFont({
    family: "AmiriQuranLatin",
    url: staticFile("fonts/amiri-quran-latin-400-normal.woff2"),
    weight: "400",
  }),
]);
