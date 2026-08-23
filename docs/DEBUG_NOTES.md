# DEBUG NOTES — گزارش دیباگ سیستماتیک پروژه

> بخش‌های «دور اول/دوم» در ادامه، گزارش تاریخی نسخهٔ داخل آرشیو اولیه‌اند. وضعیت و
> گیت‌های نسخهٔ فعلی در بخش «دور سوم» انتهای سند ثبت شده است.

این سند نتیجه‌ی بازبینی کامل پیش از تحویل است. سه سطح دفاع اعمال شد:
1. بازخوانی خط‌به‌خط همه‌ی ۴۳ فایل `.m`
2. چکرهای ایستای اختصاصی (`tools/check_mfiles.py`, `tools/check_ui_config.py`)
3. راستی‌آزمایی عددی کل pipeline با آینه‌ی پایتونی (`tools/navsim_mirror.py`)

## باگ‌های یافت‌شده و رفع‌شده

### بحرانی (عددی/الگوریتمی) — کشف‌شده با آینه‌ی پایتونی

| # | باگ | علامت | راه‌حل |
|---|---|---|---|
| 1 | **عدم‌تراز زمانی یک‌گام** بین Truth و INS در لاگ: حالت INS پس از انتگرال‌گیری (زمان t+dt) با Truth زمان t مقایسه می‌شد | خطای attitude دائمی دقیقاً برابر `ψ̇·dt` (۰٫۰۴۳°) حتی با سنسور کامل | آپدیت اندازه‌گیری/فیلتر روی حالتِ دقیق t، انتگرال‌گیری به t+dt در انتهای گام |
| 2 | **علامت جفت‌شدگی بایاس ژیرو در ماتریس F اشتباه بود** (`-C·dt` به‌جای `+C·dt` با قرارداد error = true − est) | فیلتر بایاس را با علامت برعکس تخمین می‌زد؛ خطای attitude روی ~۲۰–۳۸° گیر می‌کرد و همگرا نمی‌شد | اثبات تحلیلی `dphi_dot = +C·δbg` و اصلاح؛ تأیید با تست تخمین بایاس |
| 3 | بلاک `properties` در ۴ کلاس چند پراپرتی در یک خط داشت (نامعتبر در متلب) | خطای parse | یک پراپرتی در هر خط |

### مهم (منطقی/مدل)

| # | باگ | راه‌حل |
|---|---|---|
| 4 | Alignment با Levelling همیشه اجرا می‌شد، حتی وقتی وسیله در حرکت بود (مدل نامعتبر) | دو حالت static (Levelling) / moving (Transfer Alignment با خطای coarse قابل تنظیم) — فیلد جدید `Align.coarseMovingSigmaDeg` |
| 5 | تغییر Runtime نرخ GNSS: `nextEpoch` عقب می‌ماند و سنجش‌ها انباشته تخلیه می‌شدند | resync خودکار برنامه‌ی epoch |
| 6 | ExperimentPresets عبارت `userExpr` و تنظیمات Traj کاربر را بازنویسی می‌کرد | حفظ کامل `cfg.Traj` |
| 7 | در فاز Alignment، خروجی INS/Fused به‌صورت صفر لاگ می‌شد → spike بی‌معنا در نمودار خطا و آمار | لاگ NaN در فاز Align (نمایش gap در نمودارها) |
| 8 | سنجش‌های GNSS در فاز Alignment در لاگ نبود | لاگ GNSS در همه‌ی فازها |

### ظریف (نحو/API)

| # | باگ | راه‌حل |
|---|---|---|
| 9 | ایندکس‌گیری مستقیم از نتیجه‌ی فراخوانی تابع (`f(...)(:)`) در `test_utils.m` — غیرمجاز در متلب | تفکیک به متغیر میانی |
| 10 | سه‌پایه‌ی NED در نمای 3D مقیاس ثابت داشت و در مسیرهای بزرگ محو می‌شد | مقیاس‌پذیر با `setBounds` |
| 11 | `onLoadMat` روی فایل MAT نامربوط کرش می‌کرد | guard بر ساختار `d` |
| 12 | خطای شناور `(3x1)+(1x3)→3x3` در initNav (implicit expansion) | تبدیل هر دو به ستون |
| 13 | `strsplit(str, '\n')` روی newline واقعی کار نمی‌کرد (در متلب `'\n'` رشته‌ی دو کاراکتری است) | `strsplit(str, newline)` + `strrep` برای متن‌های خام |
| 14 | legend قبل از افزودن traceهای Attitude ساخته می‌شد (trace «Align est» جا می‌ماند) | بازسازی ترتیب ساخت legend |
| 15 | تخمین حافظه‌ی Logger با بدترین jitter بیش‌از‌حد بزرگ بود (~۴۰MB×۲) | dtMin وابسته به حالت variableDt |
| 16 | تایپو در لیبل پارامتر Gyro SF | اصلاح |

## نتیجه‌ی نهایی اعتبارسنجی (آینه‌ی پایتونی، seed ثابت)

```
[PASS] test_perfect_match   max pos err 0.0003 m, att 0.0002 deg
[PASS] test_ins_drift       gyro growth x72.9; accel 706.0 vs 706.0 m (½bt²)
[PASS] test_ekf_convergence rms pos 2.92 m, bgEst≈true, 100% within 3σ
[PASS] test_alignment       0.097 deg → 0.006 deg
[PASS] test_variable_dt     0.006 m / 0.034 m
[PASS] test_gnss_dropout    outage: fused 30 m vs INS 1615 m; recovery 1.9 m
+ sweep: 8 تراژکتوری × 3 حالت dt = 24/24 بدون NaN
+ cross-check: 93 تگ UI ↔ defaultConfig بدون مغایرت
```

## محدوده‌ی عدم پوشش در این محیط
MATLAB/Octave در sandbox نصب نیست؛ لایه‌ی GUI (uifigure) فقط با بازبینی ایستا و
تطابق API با R2020b+ بررسی شده است. بخش عددی/الگوریتمی پوشش کامل اجرایی دارد.

---

# دور دوم دیباگ — اجرای واقعی کد متلب زیر Octave 9.4

در دور دوم، GNU Octave نصب شد و **خودِ کد متلب** (نه آینه) اجرا گردید.

## یافته‌های جدید دور دوم

| # | باگ | علامت/کشف | راه‌حل |
|---|---|---|---|
| 17 | **منحنی «INS» همیشه با «Fused» یکسان بود** — هر دو از همان شیء INS پس از Correction خوانده می‌شدند، پس drift آزاد INS هرگز نمایش داده نمی‌شد | `errAttFus ≡ errAttIns` دقیقاً برابر در همه‌ی لحظات | موتور یک **INS آزاد موازی (`insPure`)** با اندازه‌گیری خام و بدون تصحیح فیلتر نگه می‌دارد؛ منحنی/مانیتور INS = insPure |
| 18 | **Transfer Alignment نسبت به attitude لحظه‌ی t=0 اعمال می‌شد** ولی alignment چند ثانیه طول می‌کشد؛ روی مسیر چرخان yaw واقعی در این مدت ~۲۱° جابه‌جا می‌شد → خطای اولیه‌ی ساختگی ~۲۰° | exp1 attitude rms ≈ 20° با وجود «Perfect IMU» | خطای coarse نسبت به **truth جاری** در هر گام اعمال می‌شود (`align.update(fm, truth)`) |
| 19 | تست EKF گاهی شاخص اولین سطر nav را روی سطر NaN می‌گرفت (به‌خاطر انباشت نقطه‌ی شناور `t+=dt` که انتقال فاز را یک گام عقب می‌اندازد) | ratio = NaN/2e13 | انتخاب اولین سطر غیر-NaN در تست |

## نتیجه‌ی اجرای واقعی کد متلب زیر Octave (seed=1)

```
test_utils            PASS   (round-trip تبدیلات)
test_perfect_match    PASS   max pos 0.0003 m / att 0.00018 deg
test_ins_drift        PASS   رشد x73؛ drift شتاب‌سنج 706.0 = ½bt² دقیق
test_ekf_convergence  PASS   rms pos 2.71 m / rms att 0.31 deg / bg est=[0.497 -0.304 0.210]
test_alignment        PASS   0.059 -> 0.040 deg
test_variable_dt      PASS   0.153 m / 0.034 m
test_gnss_dropout     PASS   در قطعی: fused 55.5 m vs INS 1438 m؛ بازگشت: 1.53 m
                              Result: 7/7 passed
```

و Experiments (Headless، مدت ۴۰ ثانیه، Circle):
```
exp1 Perfect IMU : INS rms 244.3 m / att 5.4 deg  |  Fused rms 2.75 m / att 3.3 deg
exp6 Dropout     : INS rms 231.8 m                |  Fused rms 3.04 m
exp8             : INS-only rms 250.6 m           |  GNSS/INS rms 2.71 m
```
(نکته‌ی آموزشی قشنگ: در exp1 با وجود سنسور «کامل»، خطای اولیه‌ی attitude باعث
drift شدید INS می‌شود — دقیقاً چیزی که باید دیده شود.)

- segfault کوچک هنگام خروج `octave-cli` مربوط به خود Octave است، نه کد پروژه.
- باقی‌مانده‌ی عدم پوشش: رندر واقعی GUI (uifigure) فقط در MATLAB قابل اجراست.

## پوشش پارس کامل (دور دوم)
هر ۱۷ فایل اصلی (شامل تمام کلاس‌های GUI: NavSimApp, PlotManager, View3D, DataFlowView)
زیر Octave 9.4 **کامل load/parse شدند**. دو کلاس PlotManager/View3D فقط به‌خاطر نبود
تابع `gobjects` در Octave (در متلب builtin است) نیاز به shim موقت داشتند؛ پس از آن
پارس کامل شد. نتیجه: هیچ خطای نحوی در هیچ فایل پروژه وجود ندارد.

جمع‌بندی گیت‌های نهایی دور دوم:
```
static block-balance        : OK (همه‌ی فایل‌ها)
UI <-> defaultConfig (93 tag): OK
non-ASCII code scan         : OK
mirror tests (پایتون)       : 6/6
runAllTests (کد واقعی متلب) : 7/7
GUI classes full parse      : OK
```

---

# دور سوم دیباگ — بازبینی مستقل checkout فعلی

## باگ‌های جدید رفع‌شده

1. **مرز Alignment هنوز یک گام خطای زمانی داشت**: INS در Truth زمان مرز مقداردهی
   می‌شد ولی attitude نهایی متعلق به `t-dt` بود و اولین نمونهٔ nav نیز دیر ساخته می‌شد.
   انتقال فاز اکنون پیش از پردازش نمونهٔ مرزی انجام و Alignment روی همان epoch refresh می‌شود.
2. **Snapshot زنده چند epoch را مخلوط می‌کرد**: Truth/Fused مربوط به `t` اما INS/P
   مربوط به `t+dt` بود. Log و Snapshot اکنون پیش از propagation و کاملاً هم‌زمان‌اند؛
   `engineTime` جداگانه نگهداری می‌شود.
3. **calibration یک گام دیر اعمال می‌شد**: `wc/fc` پیش از GNSS update محاسبه می‌شد.
   اکنون پس از feedback بایاس دوباره محاسبه می‌شود.
4. **عدم تطابق gravity**: Truth از free-air correction استفاده می‌کرد ولی INS مقدار ثابت
   داشت. هر دو INS اکنون gravity را از ارتفاع تخمینی خود به‌روز می‌کنند.
5. **Q شتاب ناقص بود**: بلوک cross-covariance موقعیت/سرعت (`qa*dt^2/2`) افزوده شد.
6. **`heading0` در مسیرهای خمیده نادیده گرفته می‌شد**: Circle/FigureEight/Combined3D
   اکنون طوری rotate می‌شوند که heading افقی اولیه دقیقاً مقدار کاربر باشد.
7. **تشخیص سکون Alignment فقط با سرعت** انجام می‌شد و مسیر accelerating-from-rest را
   اشتباه static می‌گرفت؛ شرط شتاب نیز اضافه شد.
8. **Runtime GNSS/Fusion**: تغییر نرخ GNSS حالا schedule را در هر دو جهت resync می‌کند،
   disable صف delay را پاک می‌کند، re-enable acquisition فوری دارد، و تغییر mode فیلتر
   state/covariance و calibration مانده را درست reset می‌کند.
9. **Config/UI**: حدود `ParamCatalog` واقعاً روی numeric editها اعمال شد؛ validator مرکزی،
   اعتبارسنجی dropout window، کنترل‌های Bias RW و rollback تغییر Runtime نامعتبر افزوده شد.
10. **Replay/Load MAT**: payload مانده از اجرای قبلی پاک می‌شود، سرعت برحسب زمان واقعی log
    است، bounds از log بارشده می‌آید و schema/dimension فایل MAT پیش از استفاده بررسی می‌شود.
11. **Test runners**: runner متلب workspace تست‌ها را جدا و در failure خطا می‌دهد؛ runner
    Python نیز exceptionها را گزارش می‌کند، exit code ناموفق دارد و `test_utils` واقعی اجرا می‌کند.
12. پروژه از آرشیو تودرتو خارج و ساختار source-first شد؛ فایل‌های محیطی ناخواستهٔ آرشیو
    وارد repo نشدند و `.gitignore` و dependency file اضافه شد.

## گیت‌های نسخهٔ فعلی

```text
static block-balance          : PASS
UI <-> defaultConfig (95 tag) : PASS
non-ASCII code scan           : PASS
Python compileall             : PASS
numerical mirror              : 8/8 PASS
MATLAB/Octave runAllTests     : 10 test تعریف‌شده؛ اجرای محلی این دور در دسترس نبود
GUI rendering                 : نیازمند MATLAB R2020b+
```

در sandbox دور سوم نصب Octave به‌علت شکست اتصال APT ممکن نشد؛ بنابراین نتیجهٔ ۷/۷ دور
دوم را نباید به ۱۰ تست جدید تعمیم داد. `runAllTests` آمادهٔ اجرای مستقیم در محیط MATLAB/
Octave است؛ دستورهای static و Python mirror برای اتصال به CI آماده‌اند.

---

# دور چهارم دیباگ — بازبینی مستقل مجدد

این دور از گزارش‌های قبلی شروع نکرد؛ edge caseهای trajectory، reset/replay، process-noise،
Bias RW و transactionهای Runtime جداگانه بازتولید شدند.

## یافته‌ها و اصلاحات

1. **Descent از نظر سینماتیکی ناسازگار بود**: clamp ارتفاع در ۵ متر، `vD` را آنی از
   ۳ به صفر می‌رساند ولی `aD=0` باقی می‌ماند. با IMU کامل در ۶۰ ثانیه خطای موقعیت
   ≈۷۸۸ m و سرعت ≈۵۵ m/s تولید می‌شد. clamp حذف شد؛ خطای همان سناریو ≈`6e-11 m` است.
2. **Turn در ورود به پیچ roll/acceleration آنی داشت**: سناریوی perfect-IMU بیست‌ثانیه‌ای
   به ≈۳۰۶ m / ۴۳.۸ m/s / ۱۸.۵° می‌رسید. ورود پیچ با smootherstep چندجمله‌ای درجه‌پنج C²
   پیاده شد؛ خطای fixed-dt آینه به ≈۰.۰۵ m و ۰.۱۷° کاهش یافت.
3. **`Fusion.qScale` روی `qbg/qba` اعمال نمی‌شد**؛ اکنون هر چهار density فرایند را
   scale می‌کند و تست نسبت covariance برای scale ده‌برابر، نسبت واریانس ۱۰۰ را می‌سنجد.
4. **خاموش‌کردن Bias، Random Walk را خاموش نمی‌کرد** و RW انباشته پس از toggle باقی
   می‌ماند. master toggle اکنون constant+RW را با هم کنترل و state انباشته را پاک می‌کند.
5. **reset، Snapshot قبلی را نگه می‌داشت**؛ `lastSnap` reset و Data Flow به waiting state
   بازمی‌گردد. وسیله/محورهای 3D مانده از اجرای قبلی نیز در reset پنهان می‌شوند.
6. **Replay و اجرای زنده هم‌زمان state داشتند**: Load/Replay اکنون اجرای زنده را pause
   می‌کند؛ پایان replay دیگر simulation قبلی را ناخواسته resume نمی‌کند و سرعت slider در
   sync preset همگام می‌شود.
7. **پیکربندی transaction نبود**: خطای UserDefined/GNSS می‌توانست engine موجود را نیمه
   mutate کند. همهٔ replacementها ابتدا محلی ساخته می‌شوند و فقط پس از موفقیت commit می‌شوند.
8. **Pending `Sim.dt/duration` روی pacing و label اجرای فعال اثر می‌گذاشت**؛ timer و status
   اکنون config فعال engine را می‌خوانند و Step نیز pending config را مانند Start اعمال می‌کند.
9. **نرخ GNSS بالاتر از polling شبیه‌سازی silently undersample می‌شد**؛ validator اکنون
   با لحاظ jitter/tworate آن را رد می‌کند. Runtime validation روی merged active config انجام
   می‌شود تا editهای ساختاری pending به‌اشتباه اعمال یا validate نشوند.
10. **Alignment کم‌سرعت ولی چرخان static تشخیص داده می‌شد**؛ شرط نرخ زاویه‌ای نیز اضافه شد.
11. Load MAT اکنون finiteness فیلدهای Truth را قبل از bounds/render بررسی می‌کند.

## اعتبارسنجی دور چهارم

```text
static block/index compatibility : PASS
UI <-> defaultConfig (95 tag)    : PASS
Python compileall                : PASS
numerical mirror                 : 8/8 PASS
perfect Descent regression       : ~7e-12 m (12 s), ~6e-11 m (60 s)
perfect Turn regression          : ~0.048 m / 0.166 deg (20 s, fixed dt)
8 trajectory x 3 dt sweep        : 24/24 finite; no discontinuity/divergence
MATLAB/Octave suite              : 10 files، assertions جدید اضافه شد؛ binary محلی موجود نیست
GUI rendering                    : نیازمند MATLAB R2020b+
```

---

# دور پنجم دیباگ — اجرای مستقل با GNU Octave WebAssembly

در این دور، baseline پاک دوباره از ابتدا بررسی شد. نصب APT به‌علت قطع اتصال مخازن Debian
ممکن نبود و CDN فایل‌های Release گیت‌هاب نیز دانلود AppImage بومی Octave 11.3.0 را قطع
می‌کرد. برای اینکه اعتبارسنجی به آینهٔ Python محدود نماند، build واقعی **GNU Octave
7.2.0 WebAssembly** از بستهٔ `@liudonghua123/octave-wasm@0.0.1` نصب شد؛ digest بستهٔ
npm بررسی و scriptهای استاندارد حذف‌شده از bundle (`assert` و `containers.Map` و وابستگی‌ها)
از source همان Octave 7.2 به فایل‌سیستم runtime افزوده شدند.

## یافته‌های جدید و بازتولید پیش از اصلاح

1. **مرز 0.5 m/s در تولید attitude**: مسیر Circle با `speed=0.5` و `radius=10`، با وجود
   نرخ واقعی 2.8648°/s، `eulDot=0` می‌داد و Alignment آن را static تشخیص می‌داد. آستانهٔ
   heading dynamics به سرعت تقریباً صفر (`1e-6`) منتقل شد؛ تست موجود `test_trajectory`
   اکنون واقعاً این regression را زیر Octave اجرا می‌کند.
2. **Snapshot فاقد timestamp نمونه بود**: پس از یک step، `phase` موجود ولی `t` غایب بود؛
   fallback تابع `getSnapshot` نیز فقط وقتی `phase` غایب بود اجرا می‌شد. `buildSnapshot`
   اکنون `sRow.t` را ثبت می‌کند و تفاوت عمدی آن با `engineTime` مستند است.
3. **ناسازگاری DCM و quaternion پس از feedback**: برای تصحیح
   `[0.1 -0.07 0.04] rad`، خطای تعامد DCM برابر `0.02333` و اختلاف آن با DCM ساخته‌شده
   از quaternion برابر `0.01164` بود. پس از استخراج quaternion نرمال، DCM از آن بازسازی
   می‌شود؛ هر دو خطا اکنون زیر `1e-12` تست می‌شوند.
4. **innovation کهنه پس از reinitialize فیلتر**: `initState` مقدارهای `lastInnov/lastNIS`
   اجرای قبلی را حفظ می‌کرد. این diagnosticها اکنون همراه state/covariance صفر می‌شوند و
   regression مستقیم دارند.
5. **آلودگی نمای زنده با MAT replay**: Start/Step payload replay را پاک می‌کردند اما اگر
   engine نیاز به configure نداشت، trail بارگذاری‌شدهٔ 3D پاک نمی‌شد. بازگشت به live view
   اکنون plot/trail و bounds فعال engine را atomically بازسازی می‌کند؛ شکست Reset/Step نیز
   replay معتبر کاربر را حذف نمی‌کند.
6. **سرعت اشتباه realtime با dt متغیر**: شمار step ثابت بر پایهٔ `Sim.dt` باعث می‌شد mode
   `tworate` با میانگین `2.5*dt`، 2.5 برابر سرعت درخواستی اجرا شود. timer اکنون budget تجمعی
   زمان شبیه‌سازی دارد و overshoot یک step را در callback بعدی جبران می‌کند.

## ابزارهای افزوده‌شده

- `tree-sitter 0.25.x` و `tree-sitter-matlab 1.3.0` به `requirements-dev.txt` افزوده شدند.
- `tools/check_matlab_syntax.py` تمام فایل‌های `.m` را با parser واقعی parse می‌کند و
  محل ERROR/missing-token را با exit code مناسب گزارش می‌دهد.
- runtime نصب‌شدهٔ audit با فرمان `octave-navsim` قابل اجرا بود؛ این runtime headless است
  و جای GUI متلب یا `octave-cli` بومی را نمی‌گیرد.

## نتیجهٔ نهایی اجرای کد واقعی `.m`

به‌علت کندی WebAssembly، suite یک‌تکه از سقف ۳۰ دقیقه عبور می‌کرد؛ هر ده فایل با workspace
و process مستقل اجرا شد و همگی exit code صفر دادند:

```text
test_utils            PASS   DCM/quaternion sync + EKF diagnostic reset
test_perfect_match    PASS   max pos 0.0000 m / max att 0.00000 deg
test_ins_drift        PASS   102.25 -> 7463.10 m (x73.0); accel 706.0 m = theory
test_ekf_convergence  PASS   RMS pos 2.66 m / RMS att 0.53 deg / 100% within 3σ
test_alignment        PASS   level error 0.059 -> 0.040 deg
test_variable_dt      PASS   jitter 0.004 m / tworate 0.454 m
test_gnss_dropout     PASS   outage 48.52 m vs INS 1438.87 m; recovery 1.57 m
test_time_alignment   PASS   first nav 1.00 s; snapshot aligned; gravity drift 0 m
test_trajectory       PASS   9 finite paths + low-speed/Descent/Turn/transaction regressions
test_runtime_updates  PASS   GNSS reschedule/re-enable + Fusion transitions
Result                PASS   10/10 files
```

گیت‌های مکمل نهایی:

```text
Tree-sitter MATLAB parse (47 files) : PASS
static block/index compatibility    : PASS
UI <-> defaultConfig (95 tags)      : PASS
non-ASCII code scan                 : PASS
Python compileall / pip check       : PASS
numerical Python mirror             : 8/8 PASS
```

محدودیت باقی‌مانده: رندر و callbackهای واقعی `uifigure/uigridlayout/timer` همچنان فقط با
MATLAB R2020b+ قابل آزمون end-to-end هستند. منطق GUI خط‌به‌خط و با parser بررسی شد، اما
این runtime WebAssembly backend گرافیکی MATLAB را فراهم نمی‌کند.
