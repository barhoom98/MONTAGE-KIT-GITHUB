import { ALL_FORMATS, Input, UrlSource } from "mediabunny";
import { staticFile } from "remotion";

// مسار ملف: إذا رابط كامل بنستعمله زي ما هو، وإلا بنعتبره داخل مجلد public
export const resolveSrc = (path: string): string =>
  /^https?:\/\//.test(path) ? path : staticFile(path.replace(/^\/+/, ""));

// مدة ملف صوت أو فيديو بالثواني (بتنحسب قبل الرندر لتحديد طول الفيديو)
export const getMediaDuration = async (path: string): Promise<number> => {
  const input = new Input({ formats: ALL_FORMATS, source: new UrlSource(resolveSrc(path)) });
  return input.computeDuration();
};

export const sec = (seconds: number, fps: number) => Math.round(seconds * fps);
