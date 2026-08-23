# ARCHITECTURE — Navigation Simulator

## 1. اصول طراحی

1. **جداسازی کامل Core از GUI**: `SimEngine` و همه مدل‌ها هیچ وابستگی به گرافیک ندارند؛
   بنابراین تست‌ها و Experimentها به‌صورت Headless با همان موتور GUI اجرا می‌شوند.
2. **Pipeline صریح در هر گام**: هر فراخوانی `step()` دقیقاً مراحل جریان داده را طی می‌کند
   و مقادیر میانی در Snapshot ثبت می‌شود (پایه‌ی Data Flow Monitor).
3. **تراز زمانی صریح**: حالت INS دقیقاً در لحظه‌ی `t` لاگ/تصحیح می‌شود و انتگرال‌گیری به
   `t+dt` در انتهای گام انجام می‌گیرد. (این تصمیم پس از کشف خطای یک‌گامی در تست‌ها گرفته شد.)
4. **Config تک‌منبع و معتبر**: یک struct (`defaultConfig`)؛ UI با `getByPath/setByPath` روی آن
   می‌خواند/می‌نویسد و `validateConfig` ورودی‌های Headless را در مرز موتور بررسی می‌کند؛
   پارامترهای Runtime-safe (`IMU.*`، `GNSS.*` و mode/Q/R در Fusion) بدون Reset اعمال
   می‌شوند؛ `Fusion.p0*` همراه تنظیمات ساختاری در Reset اعمال می‌شود.
5. **Spec-driven UI**: کل تب‌های پارامتری از روی `ParamCatalog.m` ساخته می‌شوند؛
   افزودن یک پارامتر جدید = افزودن یک خط به کاتالوگ.

## 2. اجزا

```
┌───────────────────────────────────────────────────────────────────────────┐
│ NavSimApp (uifigure)                                                      │
│ ├─ Left: ParamCatalog tabs ── Transport (Start/Pause/Stop/Reset/Step)     │
│ ├─ Right: PlotManager (Position/Velocity/Attitude/Errors/Sensors)         │
│ │         View3D (vehicle + body/nav axes + trails + GNSS points)         │
│ │         DataFlowView (stage values + EduContent)                        │
│ └─ Experiments / Logs (MAT, CSV, Replay)                                  │
└──────────────────────────────┬────────────────────────────────────────────┘
                               │ cfg (struct) + timer ticks
┌──────────────────────────────▼────────────────────────────────────────────┐
│ SimEngine  (graphics-free)                                                │
│   step():                                                                 │
│     1. TrajectoryLibrary.fh(t)            → reference-tangent trajectory  │
│     2. earthTruth (WGS84) or flat Truth   → LLA/C/w_ie/w_en/w_ib/f_b      │
│     3. IMUModel.measure → w_m,f_m (+bias/noise/SF/Mis/GM/g-sens/limits)  │
│     4. GNSSModel.update → z{tMeas,tEmit} (noise/outlier/dropout/delay)    │
│     5. Calibration: w_m-b̂g , f_m-b̂a                                    │
│     6. robust update at t, or rewind/update/repropagate fixed-lag OOSM   │
│     7. LOG: state(t), NIS/acceptance/OOSM aligned with delivery row       │
│     8. INSMechanization.step + Earth-aware ESKF.predict (t→t+dt)         │
│   phases: align → nav → done                                              │
└───────────────────────────────────────────────────────────────────────────┘
```

## 3. فریم‌ها و قراردادها

- `flat`: NED مرجع ثابت؛ `wgs84`: LLA/ECEF و NED جاری روی ellipsoid. `lla2ned/ned2lla` مختصات exact ECEF-chord در NED مرجع هستند، نه تقریب شعاع ثابت.
- Quaternion اسکالر-اول `[w;x;y;z]`، چرخش body→nav: `v_n = C_b2n · v_b`.
- در WGS84: `ω_in^n=ω_ie^n+ω_en^n` و `v̇^n=C_b^n f^b+g^n−(2ω_ie^n+ω_en^n)×v^n`.
- attitude update هم increment بدنه و هم چرخش nav frame را اعمال می‌کند؛ coning/sculling دو-sample به‌صورت streaming قابل انتخاب است.
- برداشت‌سنجی نویز سنسورها: `σ_sample = density/√dt`؛ Gauss–Markov با transition دقیق `exp(-dt/τ)` تولید می‌شود.

## 4. مدل خطای فیلتر (Error-State EKF، ۱۵ حالت)

قرارداد: **خطا = مقدار واقعی − نقطه‌ی نامی (true − est)**.

```
δṗ_ref = C_ref,current · δv
δv̇    = [f_n]×δφ − C_b^n δb_a − [2ω_ie+ω_en]×δv + gravity/rate terms + n_a
δφ̇    = −[ω_in]×δφ + C_b^n δb_g + n_g
δḃ    = −δb/τ + n_b       (Gauss–Markov)  or  n_b (random walk)
```

- nominal INS غیرخطی است و ESKF فرم استاندارد ۱۵ حالتهٔ local error را نگه می‌دارد. در WGS84، position-error در ECEF-chord/NED مرجع و velocity/attitude-error در NED جاری resolve می‌شوند.
- transition در high-fidelity تا مرتبهٔ سوم و Q با quadrature گوسی PSD گسسته می‌شود؛ مسیر flat/random-walk گسسته‌سازی legacy را برای compatibility نگه می‌دارد.
- NIS policyها: `off`، `reject`، و `adaptive` (افزایش R تا سقف `maxRInflation`). position و velocity مستقل gate می‌شوند.
- **فیدبک حلقه‌بسته**: `δx` به nominal INS و تخمین بایاس تزریق، covariance با reset Jacobian منتقل، سپس error state صفر می‌شود؛ update از Joseph form استفاده می‌کند.
- fixed-lag OOSM برای هر epoch، prior/post state، updateهای پذیرفته‌شده، raw IMU interval و config همان interval را نگه می‌دارد؛ delayed GNSS در epoch تاریخی gate و تمام بازه‌های بعدی deterministically replay می‌شوند.

## 5. توسعه‌پذیری

- مسیر جدید: یک `case` در `TrajectoryLibrary.make`.
- سنسور جدید (مثلاً Baro/Mag واقعی): کلاس مشابه GNSSModel + آپدیت در آخرین گام قبل از LOG.
- Fusion دیگر (Tightly-coupled/UKF): جایگزینی `LooselyCoupledEKF` با همان رابط
  (`initState/predict/updatePos/consumeDx/sigmas`)؛ موتور تغییر نمی‌کند.
- UI پارامتر جدید: یک سطر در `ParamCatalog`.
