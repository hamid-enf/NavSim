%TEST_EKF_CONVERGENCE GNSS+INS: bounded errors + bias estimation.
cfg = defaultConfig();
cfg.Sim.duration = 120;
cfg.Traj.type = 'FigureEight';
cfg.Fusion.mode = 'loose';
cfg.Align.enabled = true;  cfg.Align.duration = 5;
cfg.Align.applyUserErr = true;  cfg.Align.userErrDeg = [2 2 10];
cfg.IMU.gyroBiasDps = [0.5 -0.3 0.2];
cfg.IMU.accelBiasMg = [20 -15 10];
cfg.GNSS.posSigmaH = 2;  cfg.GNSS.posSigmaV = 4;

eng = SimEngine(cfg);
eng.runToEnd();
res = eng.results();

% steady-state window: last 20 s
sl = find(res.t > res.t(end) - 20);
rmsPos = sqrt(mean(res.errPosFus(sl).^2));
rmsAttDeg = rad2deg(sqrt(mean(res.errAttFus(sl).^2)));

assert(rmsPos < 3*cfg.GNSS.posSigmaH, sprintf('fused rms pos too large: %.2f m', rmsPos));
% attitude: strong convergence from the injected ~10-deg initial error
ia = find(~isnan(res.errAttFus) & res.t > cfg.Align.duration, 1, 'first');
assert(~isempty(ia), 'no nav rows found');
attRatio = res.errAttFus(end) / max(res.errAttFus(ia), eps);
assert(attRatio < 0.25, sprintf('attitude not converging: ratio %.2f', attRatio));
assert(rmsAttDeg < 2.0, sprintf('fused rms att too large: %.2f deg', rmsAttDeg));

% gyro-bias estimate should approach the true simulated bias
calBgDps = rad2deg(res.calBg(:, end));
assert(abs(calBgDps(1) - 0.5) < 0.15, sprintf('gyro bias X est %.3f vs true 0.5', calBgDps(1)));
assert(abs(calBgDps(2) + 0.3) < 0.15, sprintf('gyro bias Y est %.3f vs true -0.3', calBgDps(2)));

% filter covariance should be consistent-ish: error inside ~3 sigma (median)
sigP = res.sigP(1, sl);
errN = abs(res.fusP(1, sl) - res.truthP(1, sl));
fracIn = mean(errN < 3*sigP);
assert(fracIn > 0.90, sprintf('covariance inconsistent: only %.0f%% within 3-sigma', 100*fracIn));

fprintf('  EKF: rms pos = %.2f m, rms att = %.2f deg, bg est = [%.3f %.3f %.3f] deg/s, within-3sig %.0f%%\n', ...
    rmsPos, rmsAttDeg, calBgDps(1), calBgDps(2), calBgDps(3), 100*fracIn);
