import { Composition, Folder, Still } from "remotion";
import { AyahReel, ayahSchema, calculateAyahMetadata } from "./templates/AyahReel";
import { Cover, coverSchema } from "./templates/Cover";
import { calculateQuizMetadata, QuizReel, quizSchema } from "./templates/QuizReel";
import { calculateTipMetadata, TipReel, tipSchema } from "./templates/TipReel";
import { fontsReady } from "./theme/fonts";

// تحميل الخطوط قبل أي رندر
fontsReady.catch((e) => console.error(e));

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="Quizzawi">
        <Composition
          id="QuizReel"
          component={QuizReel}
          schema={quizSchema}
          calculateMetadata={calculateQuizMetadata}
          durationInFrames={600}
          fps={30}
          width={1080}
          height={1920}
          defaultProps={{
            channel: "quizzawi" as const,
            introSfx: "sfx/pop-modern.wav",
            category: "معلومات عامة",
            question: "ما هو أكبر كوكب في المجموعة الشمسية؟",
            options: ["زحل", "المشتري", "نبتون", "الأرض"] as [string, string, string, string],
            correct: 2,
            explanation: "المشتري أكبر كواكب المجموعة الشمسية، وحجمه أكبر من حجم الأرض بأكثر من 1300 مرة.",
            cta: "كم كان جوابك؟ اكتبه بالتعليقات",
            thinkSeconds: 5,
            musicVolume: 0.12,
            timing: { intro: 1.6, question: 4.5, reveal: 1.8, explanation: 5, outro: 2.5 },
            showSafeArea: false,
          }}
        />
      </Folder>

      <Folder name="Thamarat-Aya">
        <Composition
          id="AyahReel"
          component={AyahReel}
          schema={ayahSchema}
          calculateMetadata={calculateAyahMetadata}
          durationInFrames={900}
          fps={30}
          width={1080}
          height={1920}
          defaultProps={{
            channel: "thamarat-aya" as const,
            title: "ثمرة آية",
            episode: 1,
            sura: 70,
            ayaFrom: 19,
            ayaTo: 22,
            reciter: "Yasser_Ad-Dussary_128kbps",
            audioBase: "https://raw.githubusercontent.com/barhoom98/thamarat-aya-audio/main/audio",
            lessonsTitle: "ثمرات الآيات",
            lessons: [
              "اكتب الثمرة الأولى هون بعد مراجعة التفسير",
              "اكتب الثمرة الثانية هون بعد مراجعة التفسير",
            ],
            cta: "شارك الآية مع حدا بتحبه",
            timing: { intro: 2.5, gap: 0.6, perLesson: 4, outro: 3 },
            showSafeArea: false,
          }}
        />
      </Folder>

      <Folder name="Tips">
        <Composition
          id="Tip-Nutrition"
          component={TipReel}
          schema={tipSchema}
          calculateMetadata={calculateTipMetadata}
          durationInFrames={600}
          fps={30}
          width={1080}
          height={1920}
          defaultProps={{
            channel: "nutrition" as const,
            hook: "العدس أقوى مما بتتوقع",
            title: "3 فوائد للعدس",
            points: [
              { title: "بروتين نباتي", body: "كوب العدس المطبوخ فيه حوالي 18 غرام بروتين." },
              { title: "ألياف عالية", body: "حوالي 15 غرام ألياف بالكوب، بتساعد على الشبع والهضم." },
              { title: "حديد وفولات", body: "مصدر مهم للحديد وحمض الفوليك." },
            ],
            cta: "تابعنا لفايدة جديدة كل يوم",
            musicVolume: 0.12,
            timing: { hook: 2, perPoint: 4, cta: 2.5 },
            showSafeArea: false,
          }}
        />
        <Composition
          id="Tip-Accounting"
          component={TipReel}
          schema={tipSchema}
          calculateMetadata={calculateTipMetadata}
          durationInFrames={600}
          fps={30}
          width={1080}
          height={1920}
          defaultProps={{
            channel: "accounting" as const,
            hook: "3 أخطاء بيوقع فيها المحاسب الجديد",
            title: "نصائح للمحاسبين",
            points: [
              { title: "ما بيطابق البنك", body: "طابق كشف البنك مع الدفاتر كل شهر، مش آخر السنة." },
              { title: "بيخلط المصاريف", body: "افصل مصاريف الشركة عن المصاريف الشخصية من أول يوم." },
              { title: "ما بيحفظ المستندات", body: "كل قيد لازم يكون إله مستند مؤيد محفوظ ومرقّم." },
            ],
            cta: "تابعنا لنصيحة محاسبية كل يوم",
            musicVolume: 0.1,
            timing: { hook: 2, perPoint: 4, cta: 2.5 },
            showSafeArea: false,
          }}
        />
        <Composition
          id="Tip-Gym"
          component={TipReel}
          schema={tipSchema}
          calculateMetadata={calculateTipMetadata}
          durationInFrames={600}
          fps={30}
          width={1080}
          height={1920}
          defaultProps={{
            channel: "gym" as const,
            hook: "السكوات الصح بـ3 خطوات",
            title: "تمرين اليوم: السكوات",
            points: [
              { title: "وقفة القدمين", body: "القدمين بعرض الكتفين، والأصابع لبرّا شوي." },
              { title: "الظهر مستقيم", body: "الصدر لفوق والنظر لقدام طول الحركة." },
              { title: "النزول", body: "انزل لحد ما يصير فخذك موازي للأرض، وبعدين اطلع من كعبك." },
            ],
            cta: "جرّبه اليوم واحكيلنا بالتعليقات",
            musicVolume: 0.15,
            timing: { hook: 2, perPoint: 4, cta: 2.5 },
            showSafeArea: false,
          }}
        />
      </Folder>

      <Folder name="Covers">
        <Still
          id="Cover"
          component={Cover}
          schema={coverSchema}
          width={1080}
          height={1920}
          defaultProps={{
            channel: "quizzawi" as const,
            badge: "سؤال اليوم رقم 24",
            title: "أكبر كوكب؟",
            subtitle: "عندك 5 ثواني بس",
          }}
        />
      </Folder>
    </>
  );
};
