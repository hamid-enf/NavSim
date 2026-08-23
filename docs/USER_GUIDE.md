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

> **Runtime-safe**: پارامترهای IMU/GNSS و تنظیمات جاری Fusion (mode، Q/R و velocity update)
> در حین اجرا اعمال می‌شوند. عدم‌قطعیت‌های اولیهٔ `Fusion.p0*` فقط هنگام Reset معنا دارند.
> تغییر Trajectory / Duration / dt / P0 با پیام «applies on Reset/Start» اعلام می‌شود.

## 3. تب‌های پارامتر

- **Simulation**: dt، مدت، seed، حالت اجرا، **Variable dt** (off/jitter/tworate) برای Timing Error.
- **Trajectory**: نوع مسیر + سرعت/شعاع/نرخ صعود/دوران/جهت اولیه/شتاب یا عبارت کاربر.
  - مثال UserDefined: `[10*t; 100*sin(0.05*t); -100]` (بردار NED بر حسب `t`).
- **IMU**: فعال‌سازی و مقادیر Bias/Noise/SF/Misalignment و Bias Random Walk برای ژیرو و شتاب‌سنج.
- **GNSS**: نرخ، نویز، بایاس، سرعت، Dropout (`dropoutText` مثل `'30 60; 90 100'`)، Outlier، Delay.
- **INS & Align**: خطای اولیه موقعیت/سرعت، مرجع ژئودتیک، تنظیمات Alignment و خطای اولیه کاربر.
- **Fusion**: حالت `ins` (INS Only) یا `loose` (GNSS+INS)، چگالی‌های نویز فرایند،
  عدم‌قطعیت‌های اولیه `P0`، مقیاس‌های Q/R، فعال‌سازی سنجش سرعت.
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

- Alignment دو حالت دارد: اگر در شروع \|v0\| ≤ 1 m/s و \|a0\| ≤ 0.1 m/s² باشد
  (سکون واقعی)، Levelling با شتاب‌سنج + قطب‌نما انجام می‌شود (همگرایی 1/√n در
  نمودار Attitude دیده می‌شود)؛
  اگر وسیله در حرکت باشد، «Transfer Alignment» مدل می‌شود (حدس درشت با سیگمای
  قابل تنظیم) و اصلاح نهایی به Fusion در حین مانور واگذار می‌شود.
- مدل زمین‌تخت است؛ برای مسیرهای چندکیلومتری دقیق است، برای قاره‌پیمایی نه.
- Gyrocompassing مدل نشده؛ heading اولیه از magnetometer-stub می‌آید.
