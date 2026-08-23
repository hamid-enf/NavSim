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
