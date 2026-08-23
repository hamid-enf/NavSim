classdef ExperimentPresets
%EXPERIMENTPRESETS Ready-made experiments (Section 14 of the spec).
methods (Static)
    function names = list()
        names = { ...
          '1. Perfect IMU (no IMU errors)', ...
          '2. Gyro Bias', ...
          '3. Accel Bias', ...
          '4. IMU Noise', ...
          '5. GNSS Noise (perfect IMU)', ...
          '6. GNSS Dropout', ...
          '7. Initial Alignment Error', ...
          '8. INS Only vs GNSS/INS', ...
          '9. Variable dt', ...
          '10. Combined Errors'};
    end

    function txt = description(idx)
        T = { ...
        ['Perfect IMU: همه خطاهای IMU صفر. انتظار: خطای Fused ≈ خطای GNSS noise،\n' ...
         'INS drift تقریباً صفر. مرجع سلامت سیستم است.'], ...
        ['Gyro Bias روشن (1 deg/s)، بقیه خاموش. در حالت INS Only خطا با زمان\n' ...
         'رشد می‌کند (چرخه Schuler/رشد درجه دوم). فیلتر بایاس را تخمین می‌زند.'], ...
        ['Accel Bias روشن (50 mg)، بقیه خاموش. خطای موقعیت ≈ 1/2*b*t^2 در INS Only.\n' ...
         'Fusion خطا را کران‌دار نگه می‌دارد.'], ...
        ['فقط نویز IMU (ARW بالا). در INS Only خطا به‌صورت تصادفی رشد می‌کند؛\n' ...
         'با Fusion، رشد بین-to وصل GNSS محدود می‌شود.'], ...
        ['IMU کامل، اما نویز GNSS بزرگ (10 m). دقت Fused توسط R و نویز GNSS\n' ...
         'محدود می‌شود؛ سیگماهای فیلتر را تماشا کنید.'], ...
        ['Dropout در بازه [30 60] و [90 100] ثانیه. در قطعی، تخمین روی INS\n' ...
         'سوار است و drift می‌کند؛ پس از بازگشت GNSS سریع همگرا می‌شود.'], ...
        ['خطای اولیه Roll/Pitch/Yaw = [2 2 10] deg بدون Alignment.\n' ...
         'EKF در حرکت، خطای وضعیت را شناسایی و تصحیح می‌کند.'], ...
        ['اجرای دوتایی خودکار: INS Only در برابر GNSS+INS با خطاهای متوسط.\n' ...
         'نمودار مقایسه و جدول آماری هر دو حالت را نشان می‌دهد.'], ...
        ['dt متغیر (jitter 50%). INS باید در هر دو حالت سازگار بماند؛\n' ...
         'تأثیر Timing Error را ببینید.'], ...
        ['همه خطاها همزمان: بایاس+نویز+SF+Misalignment+GNSS outlier/dropout.\n' ...
         'سناریوی واقعی. پایداری Fused را با INS Only مقایسه کنید.']};
        txt = T{idx};
    end

    function cfg = apply(cfg, idx)
        % Start from defaults so experiments are reproducible.
        base = defaultConfig();
        base.Traj            = cfg.Traj;            % keep user's trajectory choice (incl. userExpr)
        base.Sim.duration    = cfg.Sim.duration;
        base.Sim.seed        = cfg.Sim.seed;
        cfg = base;
        I = cfg.IMU;
        allOff = struct('useGyroBias',false,'useGyroNoise',false,'useGyroSF',false, ...
            'useGyroMis',false,'useAccelBias',false,'useAccelNoise',false, ...
            'useAccelSF',false,'useAccelMis',false);
        fn = fieldnames(allOff);
        cfg.Align.applyUserErr = false;
        cfg.Align.enabled = true; cfg.Align.duration = 5;
        % Presets isolate the named error source; do not silently inject a
        % random moving-platform or magnetometer alignment error.
        cfg.Align.magHeadingSigmaDeg = 0;
        cfg.Align.coarseMovingSigmaDeg = 0;
        switch idx
            case 1   % Perfect IMU
                for i=1:numel(fn), cfg.IMU.(fn{i}) = false; end
            case 2   % Gyro Bias
                for i=1:numel(fn), cfg.IMU.(fn{i}) = false; end
                cfg.IMU.useGyroBias = true;
                cfg.IMU.gyroBiasDps = [1 -0.7 0.5];
            case 3   % Accel Bias
                for i=1:numel(fn), cfg.IMU.(fn{i}) = false; end
                cfg.IMU.useAccelBias = true;
                cfg.IMU.accelBiasMg = [50 -30 20];
            case 4   % IMU Noise
                for i=1:numel(fn), cfg.IMU.(fn{i}) = false; end
                cfg.IMU.useGyroNoise = true;  cfg.IMU.gyroARWDpsHz = 0.1;
                cfg.IMU.useAccelNoise = true; cfg.IMU.accelVRW = 0.1;
            case 5   % GNSS Noise (perfect IMU)
                for i=1:numel(fn), cfg.IMU.(fn{i}) = false; end
                cfg.GNSS.posSigmaH = 10; cfg.GNSS.posSigmaV = 15;
                cfg.Fusion.rScale = 1;
            case 6   % GNSS Dropout
                cfg.GNSS.useDropout = true;
                cfg.GNSS.dropoutText = '30 60; 90 100';
            case 7   % Initial Alignment Error
                cfg.Align.enabled = false;
                cfg.Align.applyUserErr = true;
                cfg.Align.userErrDeg = [2 2 10];
            case 8   % INS vs GNSS/INS (handled by caller: two runs)
                cfg.IMU.gyroBiasDps = [0.5 -0.3 0.2];
            case 9   % Variable dt
                cfg.Sim.variableDt = 'jitter';
                cfg.Sim.dtJitter = 0.5;
            case 10  % Combined
                cfg.IMU.useGyroSF = true;  cfg.IMU.useGyroMis = true;
                cfg.IMU.useAccelSF = true; cfg.IMU.useAccelMis = true;
                cfg.GNSS.useOutlier = true; cfg.GNSS.outlierProb = 0.02;
                cfg.GNSS.useDropout = true; cfg.GNSS.dropoutText = '50 70';
                cfg.Sim.variableDt = 'jitter'; cfg.Sim.dtJitter = 0.3;
        end
        if idx == 8
            cfg.Fusion.mode = 'ins';   % first run: INS only
        else
            cfg.Fusion.mode = 'loose';
        end
    end

    function res = runHeadless(cfg)
        eng = SimEngine(cfg);
        eng.runToEnd();
        res = eng.results();
    end

    function m = metrics(res)
        % Summary metrics (post-alignment rows only).
        ia = find(~isnan(res.alignEst(1,:)), 1, 'last');
        if isempty(ia), ia = 0; end
        sl = (ia+1):res.n;
        if isempty(sl), sl = 1:res.n; end
        m.rmsPosFus  = sqrt(mean(res.errPosFus(sl).^2));
        m.maxPosFus  = max(res.errPosFus(sl));
        m.finPosFus  = res.errPosFus(end);
        m.rmsPosIns  = sqrt(mean(res.errPosIns(sl).^2));
        m.rmsAttDegF = rad2deg(sqrt(mean(res.errAttFus(sl).^2)));
        m.dur        = res.t(end);
    end
end
end
