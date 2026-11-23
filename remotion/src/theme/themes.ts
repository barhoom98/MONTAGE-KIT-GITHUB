import { z } from "zod";

// هوية كل قناة بمكان واحد. ألوان كويزاوي هي ألوان اللوغو المعتمدة.
// ألوان القنوات الثانية مقترحة: غيّرها هون وبتتغير بكل القوالب.

export type Theme = {
  id: ChannelId;
  name: string; // اسم القناة كما بيظهر على الشاشة
  bgTop: string; // لون الخلفية فوق
  bgBottom: string; // لون الخلفية تحت
  card: string; // لون الكروت والخيارات
  primary: string; // اللون الأساسي (العناوين والإبراز)
  accent: string; // لون ثانوي (أرقام وشارات)
  text: string; // لون النص على الخلفية
  cardText: string; // لون النص على الكروت
  correct: string; // لون الجواب الصح
  muted: string; // لون العناصر الباهتة
};

export const channelIds = ["quizzawi", "thamarat-aya", "nutrition", "accounting", "gym"] as const;
export type ChannelId = (typeof channelIds)[number];
export const zChannel = z.enum(channelIds);

export const THEMES: Record<ChannelId, Theme> = {
  quizzawi: {
    id: "quizzawi",
    name: "كويزّاوي",
    bgTop: "#5B16B8",
    bgBottom: "#25004A",
    card: "#FFF5D9",
    primary: "#FFD900",
    accent: "#FF9E00",
    text: "#FFF5D9",
    cardText: "#25004A",
    correct: "#2BD47D",
    muted: "rgba(255,245,217,0.35)",
  },
  "thamarat-aya": {
    id: "thamarat-aya",
    name: "ثمرة آية",
    bgTop: "#0E4A3A",
    bgBottom: "#062A21",
    card: "#F7F1E3",
    primary: "#D4AF37",
    accent: "#E9C46A",
    text: "#F7F1E3",
    cardText: "#062A21",
    correct: "#D4AF37",
    muted: "rgba(247,241,227,0.4)",
  },
  nutrition: {
    id: "nutrition",
    name: "قناة التغذية",
    bgTop: "#2E8B3E",
    bgBottom: "#0F3D1C",
    card: "#FFFBEA",
    primary: "#C6F432",
    accent: "#FF8C42",
    text: "#FFFBEA",
    cardText: "#0F3D1C",
    correct: "#C6F432",
    muted: "rgba(255,251,234,0.4)",
  },
  accounting: {
    id: "accounting",
    name: "قناة المحاسبة",
    bgTop: "#123A6B",
    bgBottom: "#071A33",
    card: "#F4F7FB",
    primary: "#2DD4BF",
    accent: "#F4B942",
    text: "#F4F7FB",
    cardText: "#071A33",
    correct: "#2DD4BF",
    muted: "rgba(244,247,251,0.4)",
  },
  gym: {
    id: "gym",
    name: "قناة الجيم",
    bgTop: "#2A2A2E",
    bgBottom: "#0B0B0D",
    card: "#F2F2F2",
    primary: "#FF3B3B",
    accent: "#FFB703",
    text: "#F2F2F2",
    cardText: "#0B0B0D",
    correct: "#FF3B3B",
    muted: "rgba(242,242,242,0.4)",
  },
};

export const getTheme = (id: ChannelId): Theme => THEMES[id];
