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
│     1. TrajectoryLibrary.fh(t)            → truth {p,v,a,eul,eulDot}      │
│     2. w= T(eul)eulDot ; f= C'(a-g)       → IMU truth (body frame)        │
│     3. IMUModel.measure                   → w_m, f_m (+bias/noise/SF/Mis) │
│     4. GNSSModel.update                   → z (rate/noise/outlier/delay)  │
│     5. Calibration: w-m-b̂g , f-m-b̂a                                     │
│     6. [Fusion] measurement update روی حالتِ t                            │
│     7. LOG: state(t) aligned with truth(t)                                │
│     8. INSMechanization.step (q⊗Δq, ذوزنقه‌ای) + EKF.predict (t→t+dt)    │
│   phases: align → nav → done                                              │
└───────────────────────────────────────────────────────────────────────────┘
```

## 3. فریم‌ها و قراردادها

- **NED محلی** با مرجع ژئودتیک (`INS.refLat/refLon/refH`)؛ تبدیل دوطرفه `lla2ned/ned2lla` (شعاع انحنای WGS84).
- Quaternion اسکالر-اول `[w;x;y;z]`، چرخش body→nav: `v_n = C_b2n · v_b`.
- اویلر ZYX (roll, pitch, yaw)؛ نرخ‌ها: `w_b = T(eul)·eulDot`.
- نیروی ویژه: `f_b = C_n2b·(a_n − g_n)` با `g_n=[0;0;+g]`.
- برداشت‌سنجی نویز سنسورها: `σ_sample = density/√dt` (سازگار با dt متغیر).

## 4. مدل خطای فیلتر (Error-State EKF، ۱۵ حالت)

قرارداد: **خطا = مقدار واقعی − نقطه‌ی نامی (true − est)**.

```
δṗ   = δv
δv̇   = [f_n]×·δφ − C·δb_a + n_a
δφ̇   = +C·δb_g + n_g          ← علامت مثبت با این قرارداد (در تست‌ها تأیید شد)
δḃ_g = n_bg ,  δḃ_a = n_ba
```

- آپدیت: سنجش موقعیت GNSS (و اختیاری سرعت) روی حالت در لحظه‌ی t.
- **فیدبک حلقه‌بسته**: پس از هر آپدیت، `δx` به INS و کالیبراسیون بایاس‌ها تزریق و صفر می‌شود.
- `P` با فرم Joseph به‌روز و متقارن نگه داشته می‌شود؛ Q گسسته شامل
  `Qpp=q_a·dt³/3`، `Qpv=q_a·dt²/2` و `Qvv=q_a·dt` است.

## 5. توسعه‌پذیری

- مسیر جدید: یک `case` در `TrajectoryLibrary.make`.
- سنسور جدید (مثلاً Baro/Mag واقعی): کلاس مشابه GNSSModel + آپدیت در آخرین گام قبل از LOG.
- Fusion دیگر (Tightly-coupled/UKF): جایگزینی `LooselyCoupledEKF` با همان رابط
  (`initState/predict/updatePos/consumeDx/sigmas`)؛ موتور تغییر نمی‌کند.
- UI پارامتر جدید: یک سطر در `ParamCatalog`.
