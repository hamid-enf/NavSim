# Navigation Simulator (GNSS/INS Educational Lab)

شبیه‌ساز کاملاً **تعاملی، گرافیکی و آموزشی** Navigation در متلب:
جریان کامل داده از **Sensor** تا **Navigation Solution** به‌صورت زنده قابل مشاهده است
و پارامترهای سیستم در **Runtime** قابل تغییرند.

```
Trajectory → Truth → IMU ─┐                ┌→ (raw, برای نمایش)
                          ├→ Calibration → INS → Prediction → Fusion → Estimate → Error Analysis
Trajectory → Truth → GNSS ┴──────────────────────────┘
```

## شروع سریع

```matlab
cd NavSim
main            % راه‌اندازی GUI
```

اجرای تست‌های اعتبارسنجی عددی (بدون GUI):

```matlab
cd NavSim
runAllTests
```

## ویدیوی آموزشی (فارسی، 4K)

یک کلیپ آموزشی انیمیشنی و گرافیکی (~۱۵:۵۱، 3840×2160) که کل جریان داده —
از تولید مسیر تا تلفیق و تحلیل خطا — را قدم‌به‌قدم با گویش فارسی، فرمول‌ها و
چارت‌های واقعی توضیح می‌دهد. فایل نهایی از طریق **GitHub Release** این مخزن
دانلود می‌شود و سورس کامل ساخت آن در پوشه‌ی [`video/`](video/) قرار دارد.

## قابلیت‌ها (نگاشت به الزامات)

| بخش | پیاده‌سازی |
|---|---|
| Trajectory | 9 مسیر: Straight، Circle، FigureEight، Acceleration، Climb، Descent، Turn، Combined3D، UserDefined (عبارت دلخواه `p(t)`) |
| IMU | Bias/ARW/VRW/SF/Misalignment + بایاس Gauss–Markov، g-sensitivity، saturation و quantization — همه در Runtime |
| GNSS | نرخ، نویز H/V، بایاس، سرعت، Dropout، Outlier (موقعیت و سرعت)، delay با epoch فیزیکی مستقل + خطای همبستهٔ Gauss–Markov (مانند multipath) |
| INS | مکانیزاسیون Quaternion در دو حالت `flat` و **WGS84 local-level**؛ نرخ زمین/ترابرد، Coriolis، coning/sculling و **dt متغیر** |
| Alignment | Levelling با شتاب‌سنج + قطب‌نما (stub)، خطای اولیه کاربر، نمایش همگرایی |
| Fusion | ESKF حلقه‌بستهٔ ۱۵ حالته با دینامیک زمین، گسسته‌سازی مرتبهٔ بالاتر، Joseph/reset، NIS robust gating و fixed-lag OOSM |
| Aiding | Baro (ارتفاع‌سنج بارومتریک با بایاس/نویز/GM) و ZUPT (به‌روزرسانی سرعت صفر در توقف) — همه در Runtime و بهینه برای سناریوهای تونل/بدون GNSS |
| Error Injection | تب Errors: همه منابع خطا با یک کلیک فعال/غیرفعال |
| Visualization | Position / Velocity / Attitude / Errors / Sensors + نمای 3D (وسیله، محورهای Body و Nav، مسیرها، نقاط GNSS) |
| Real-Time | Start / Pause / Stop / Reset / Step، حالت Real-time و Fast، اسلایدر سرعت |
| Data Flow Monitor | پنل زنده‌ی مراحل + مقادیر فعلی هر مرحله (Gyro, Lat/Lon/Alt, ...) |
| Educational Mode | کلیک روی هر مرحله → توضیح کوتاه: چیست؟ ورودی/خروجی؟ معادله؟ خطاها؟ |
| Experiments | ۱۰ آزمایش آماده با اجرای Headless و مقایسه‌ی آماری |
| Logging | ذخیره MAT/CSV + Replay انیمیشنی |
| Tests | ۱۴ تست MATLAB/Octave (`runAllTests`) + ۹ تست آینهٔ عددی Python |

## ساختار پوشه‌ها

```
NavSim/
  main.m                  launcher
  startup.m               addpath همه زیرپوشه‌ها
  runAllTests.m           اجرای مجموعه تست
  simulation/             defaultConfig.m, SimEngine.m      (موتور بدون گرافیک)
  trajectory/             TrajectoryLibrary.m
  imu/                    IMUModel.m
  gnss/                   GNSSModel.m, BaroModel.m
  ins/                    INSMechanization.m
  alignment/              Alignment.m
  fusion/                 LooselyCoupledEKF.m
  visualization/          PlotManager.m, View3D.m
  ui/                     NavSimApp.m, ParamCatalog.m, DataFlowView.m,
                          EduContent.m, ExperimentPresets.m
  logging/                NavLogger.m
  utils/                  quaternion/euler/DCM/LLA/NED + setByPath/getByPath ...
  tests/                  test_*.m
  docs/                   ARCHITECTURE.md, USER_GUIDE.md, EXPERIMENTS.md
```

## مدل‌ها و فرض‌های باقیمانده (شفاف‌سازی)

- `INS.earthModel='flat'` مسیر آموزشی/سازگار قبلی را نگه می‌دارد. در حالت `wgs84`، مکانیزاسیون local-level بر پایهٔ ECEF/LLA دقیق، نرخ زمین و transport، Coriolis و گرانش عرض/ارتفاع اجرا می‌شود.
- برای بازتولید رفتار legacy: `earthModel='flat'`، `useConingSculling=false`، `Fusion.robustMode='off'` و `Fusion.useOOSM=false` را انتخاب کنید.
- ESKF همچنان فرم استاندارد **۱۵ حالتهٔ خطای کوچک** است؛ nominal state غیرخطی است ولی covariance ناگزیر پیرامون آن linearize می‌شود. lever-arm، GNSS clock/raw pseudorange، precession/nutation، tides و مدل gravity harmonics جزو دامنه نیستند.
- trajectoryها در صفحهٔ مماس مرجع author می‌شوند و در حالت WGS84 به local-level جاری نگاشت می‌شوند؛ این ابزار شبیه‌ساز قاره‌پیما یا orbital navigator نیست.
- OOSM فقط epochهایی را که داخل `Fusion.oosmLag` و دقیقاً روی یکی از epochهای ذخیره‌شدهٔ IMU باشند rewind/replay می‌کند؛ نمونهٔ قدیمی‌تر به‌طور صریح reject و log می‌شود.
- Heading در Alignment هنوز از «قطب‌نمای مغناطیسی» مدل‌شده می‌آید؛ gyrocompassing کامل مدل نشده است.
- همگرایی کامل ۱۵-state ESKF با سنجش فقط‌موقعیت نیازمند مانور است (قابل مشاهده در Exp 7).

## اعتبارسنجی و توسعه

مجموعهٔ اصلی ۱۳ تست Headless دارد و در صورت شکست هر تست، `runAllTests` با خطا خاتمه
می‌یابد (مناسب CI):

```matlab
startup
runAllTests
```

برای بررسی سریع بدون MATLAB/Octave، آینهٔ عددی Python و چکرهای ایستا را اجرا کنید:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/check_matlab_syntax.py  # parse واقعی تمام فایل‌های .m با Tree-sitter
python tools/check_mfiles.py         # قواعد سازگاری MATLAB R2020b
python tools/check_ui_config.py
python tools/run_mirror_tests.py
```

آینهٔ فعلی ۸ گروه تست را پوشش می‌دهد: تبدیلات و heading مسیرها، Perfect match، drift
ژیرو/شتاب‌سنج، همگرایی EKF، Alignment، `dt` متغیر، GNSS dropout، مقیاس Q/Bias-RW و
رگرسیون‌های تراز زمانی، gravity، Descent و Turn. این دستورها exit-code مناسب CI دارند.
تست‌های MATLAB علاوه بر این موارد، زمان‌بندی Runtime GNSS، تغییر حالت Fusion،
اعتبارسنجی Config، همهٔ ۹ مسیر و سازگاری Snapshot زنده را نیز بررسی می‌کنند.

> **INS آزاد موازی**: خروجی «INS» همیشه مسیر drift خام (بدون تصحیح فیلتر) را نشان می‌دهد،
> حتی وقتی Fusion فعال است — مقایسهٔ زندهٔ INS در برابر Fused هستهٔ دمو است.

نسخهٔ MATLAB مورد نیاز: **R2020b یا جدیدتر** (`uifigure`/`uigridlayout`). هسته و تست‌های
عددی با GNU Octave نیز سازگار طراحی شده‌اند، اما GUI به MATLAB نیاز دارد. اگر متن فارسی
در ویندوز به‌هم‌ریخته دیده شد، Encoding فایل‌ها را UTF-8 نگه دارید.
