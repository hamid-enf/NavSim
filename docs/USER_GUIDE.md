# USER GUIDE — راهنمای کاربر

## 1. اجرا

```matlab
cd NavSim
main          % باز شدن GUI
```

اولین اجرا: مسیر پیش‌فرض Circle با IMUِ دارای بایاس/نویز و GNSS 1Hz فعال است؛
«Start» را بزنید و تب‌های **Position / Errors / 3D View / Data Flow** را ببینید.

## 2. کنترل‌های اجرا (Transport)

| دکمه | عمل |
|---|---|
| Start | شروع/ادامه؛ اگر پارامتر ساختاری عوض شده باشد، خودکار Reset+Configure می‌کند |
| Pause | توقف موقت (داده‌ها حفظ می‌شوند) |
| Stop | توقف؛ داده‌ها برای ذخیره/بازبینی باقی می‌مانند |
| Reset | بازگشت به t=0 با همان Config (پاک شدن نمودارها) |
| Step | اجرای یک گام IMU (عالی برای تدریس گام‌به‌گام) |
| Speed | 0.1x تا 20x در حالت Real-time |
| Sim mode | `realtime` (با ساعت دیواری) یا `fast` (حداکثر سرعت) |

> **Runtime-safe**: پارامترهای IMU/GNSS و تنظیمات جاری Fusion (mode، Q/R، velocity update، robust gate و OOSM window)
> در حین اجرا اعمال می‌شوند. عدم‌قطعیت‌های اولیهٔ `Fusion.p0*` فقط هنگام Reset معنا دارند.
> تغییر Trajectory / Duration / dt / P0 با پیام «applies on Reset/Start» اعلام می‌شود.

## 3. تب‌های پارامتر

- **Simulation**: dt، مدت، seed، حالت اجرا، **Variable dt** (off/jitter/tworate) برای Timing Error.
- **Trajectory**: نوع مسیر + سرعت/شعاع/نرخ صعود/دوران/جهت اولیه/شتاب یا عبارت کاربر.
  - مثال UserDefined: `[10*t; 100*sin(0.05*t); -100]` (بردار NED بر حسب `t`).
- **IMU**: Bias/Noise/SF/Misalignment و driving noise بایاس؛ انتخاب Random Walk یا Gauss–Markov، correlation time، gyro g-sensitivity، saturation و quantization.
  سوئیچ اصلی Bias، مؤلفهٔ ثابت و مؤلفهٔ stochastic همان سنسور را با هم فعال/غیرفعال می‌کند.
- **GNSS**: نرخ، نویز، بایاس، سرعت، Dropout (`dropoutText` مثل `'30 60; 90 100'`)، Outlier و Delay. هر نمونه `tMeas` فیزیکی و `tEmit` تحویل مستقل دارد.
  نرخ GNSS نباید از کمترین نرخ polling شبیه‌سازی (با درنظرگرفتن variable dt) بیشتر باشد.
  **خطای همبستهٔ GM** (`useGmNoise`): خطای Gauss–Markov با σ=gmSigma و τ=gmTau به اندازه‌گیری اضافه می‌شود (مدل سادهٔ multipath).
  این خطا در R منعکس *نمی‌شود*؛ فیلترِ بدون robust mode دچار بیش‌اطمینانی می‌شود — `robustMode=adaptive|reject` را مقایسه کنید.
  **Outlier سرعت**: با `outlierVelSigma>0`، دور زدن epoch کامل (موقعیت *و* سرعت) خراب می‌شود.
- **Baro** (تب جدید): ارتفاع‌سنج بارومتریک با نرخ/نویز/بایاس ثابت و درِف Gauss–Markov.
  آپدیت اسکالر ارتفاع با گیت NIS مستقل (1 درجه آزادی). برای سناریوهای بدون GNSS (تونل/اتاق پرواز) عمود کانال را کران‌دار می‌کند.
- **INS & Align**: خطای اولیه، مرجع ژئودتیک، `flat|wgs84`، Earth/transport/Coriolis، coning/sculling و Alignment.
- **Fusion**: حالت `ins|loose`، چگالی‌های نویز، `P0` و Q/R؛ robust NIS mode/gates، adaptive-R cap و fixed-lag OOSM/window.
  **ZUPT**: پس از `zuptHoldS` ثانیه سکونِ آشکارشده (`|‖f‖−g| < zuptAccelG` و `‖w‖ < zuptRateDps`)، شبه‌مشاهدهٔ v=0 با σ=zuptSigma هر گام تزریق می‌شود.
  برای خودرو (توقف پشت چراغ) و پیاده‌روی (PDR) خطای INS را عملاً صفر نگه می‌دارد؛ ستون `zupt` در LOG (1=اعمال، 2=رد گیت).
- **Errors**: همه‌ی سوئیچ‌های خطا در یک صفحه (برای دمو سریع).

## 4. نمایش‌ها

- **Position/Velocity/Attitude**: Truth (سیاه)، INS (آبی)، GNSS (نقطه نارنجی)، Fused (سبز).
- **Errors**: نُرم خطای موقعیت/سرعت/وضعیت برای INS و Fused + مؤلفه‌های خطای Fused.
- **Sensors**: خروجی واقعی (خاکستری) در برابر سنجش‌شده (قرمز) ژیرو/شتاب‌سنج.
- **3D View**: وسیله با محورهای Body (x قرمز، y سبز، z آبی)، محورهای NED در مبدأ،
  مسیر واقعی/تخمینی و نقاط GNSS.
- **Data Flow**: مقادیر زنده‌ی هر مرحله + پنل آموزشی؛ روی هر مرحله کلیک کنید
  (ورودی/خروجی، معادله، خطاهای مؤثر).

## 5. Experiments

۱۰ سناریوی آماده در تب Experiments:
- **Apply to Config**: پیکربندی به UI منتقل می‌شود تا زنده تماشا کنید.
- **Run Headless & Compare**: اجرای فوری بدون GUI + نمودار نُرم خطا + جدول RMS/Max/Final.
  آزمایش ۸ دو اجرا (`INS Only` در برابر `GNSS/INS`) را هم‌زمان مقایسه می‌کند.

## 6. Logging و Replay

- تب Logs → **Save MAT / Save CSV**.
- **Load MAT & view**: بارگذاری لاگ قبلی و نمایش روی نمودارها + **Replay animation**
  (حرکت وسیله در 3D View با سرعت قابل تنظیم).

## 7. سناریوهای پیشنهادی کلاس درس

1. Perfect IMU (Exp 1) → خطا ≈ نویز GNSS؛ اعتبارسنجی سیستم.
2. فقط Gyro Bias (Exp 2) در حالت INS Only → رشد درجه‌دوم خطا؛ سپس به `loose` بروید
   و تخمین بایاس (`calBg` در Data Flow) را دنبال کنید.
3. GNSS Dropout (Exp 6) → افزایش σ در Data Flow هنگام قطعی + بازگشت سریع.
4. Alignment: سرعت=0، مدت Alignment زیاد/کم → منحنی همگرایی در تب Attitude.
5. Variable dt (Exp 9) → مقایسه با حالت عادی.

## 8. نکات/محدودیت‌های مدل (مهم برای تفسیر نتایج)

- Alignment دو حالت دارد: اگر در شروع سرعت، شتاب و نرخ زاویه‌ای همگی کم باشند
  (آستانه‌ها: 1 m/s، 0.1 m/s² و 0.1°/s)، Levelling با شتاب‌سنج + قطب‌نما انجام
  می‌شود (همگرایی 1/√n در
  نمودار Attitude دیده می‌شود)؛
  اگر وسیله در حرکت باشد، «Transfer Alignment» مدل می‌شود (حدس درشت با سیگمای
  قابل تنظیم) و اصلاح نهایی به Fusion در حین مانور واگذار می‌شود.
- حالت `flat` مدل آموزشی سابق است. حالت `wgs84` از ellipsoid، NED جاری، نرخ زمین/ترابرد، Coriolis و gravity عرض/ارتفاع استفاده می‌کند. برای legacy کامل، coning/sculling، robust gating و OOSM را نیز خاموش کنید.
- ESKF استاندارد ۱۵ حالته و local-linear است؛ lever arm، clock/pseudorange خام، tide، precession/nutation و gravity harmonics مدل نشده‌اند.
- trajectory هنوز در tangent plane مرجع تعریف و سپس به WGS84 نگاشت می‌شود؛ بنابراین هدف آن آموزش local navigation است، نه مسیر قاره‌ای/فضایی.
- delayed GNSS تنها داخل history window و روی epoch ذخیره‌شده rewind می‌شود؛ وضعیت accepted/rejected/too-old، NIS و `tMeas` در log و Data Flow قابل مشاهده است.
- Gyrocompassing کامل مدل نشده؛ heading اولیه از magnetometer-stub می‌آید.
