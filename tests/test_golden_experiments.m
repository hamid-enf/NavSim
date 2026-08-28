function test_golden_experiments
%TEST_GOLDEN_EXPERIMENTS Guard the reference behavior quoted in
% docs/EXPERIMENTS.md (and the educational video) against silent drift.
% Tolerances are intentionally loose: this is a behavioral guardrail, not a
% bit-exact regression test (RNG sequences differ between MATLAB and the
% Python mirror, which is where the documented reference numbers come from).

% --- GNSS dropout reference (EXPERIMENTS.md): while GNSS is out, the fused
% --- solution must stay far below unaided INS and must recover after return.
cfg = defaultConfig();
cfg.Sim.seed = 1;
cfg.Sim.duration = 120;
cfg.Traj.type = 'Circle';
cfg.Fusion.mode = 'loose';
cfg.Align.enabled = true;  cfg.Align.duration = 5;
cfg.GNSS.useDropout = true;
cfg.GNSS.dropoutText = '40 70';
eng = SimEngine(cfg);
eng.runToEnd();
res = eng.results();

inOut = res.t >= 55 & res.t <= 69;
post  = res.t >= 85;
mFus  = mean(res.errPosFus(inOut));
mPost = mean(res.errPosFus(post));
cfgI = cfg; cfgI.Fusion.mode = 'ins';
resI = ExperimentPresets.runHeadless(cfgI);
mIns = mean(resI.errPosIns(inOut));
assert(mIns > 3*mFus, ...
    sprintf('dropout: fused no longer beats INS (INS %.0f m, fused %.0f m)', mIns, mFus));
assert(mFus < 60, ...
    sprintf('dropout: fused error grew too large: %.1f m (doc ~30 m)', mFus));
assert(mPost < 6, ...
    sprintf('post-recovery: fused did not recover: %.1f m (doc ~1.9 m)', mPost));
fprintf('  golden dropout: INS %.0f m, Fused %.1f m, post %.2f m\n', mIns, mFus, mPost);

% --- experiment 2 reference: gyro-bias learning.
% --- Assert convergence to the TRUE injected bias (RNG-tolerant): MATLAB and
% --- the Python mirror use different RNGs, so assert against the injected
% --- value, not a specific run's numbers.
cfg2 = defaultConfig();
cfg2.Sim.seed = 1;
cfg2.Sim.duration = 120;
cfg2.Traj.type = 'FigureEight';
cfg2.Fusion.mode = 'loose';
cfg2.Align.enabled = true;  cfg2.Align.duration = 5;
cfg2.Align.applyUserErr = true;  cfg2.Align.userErrDeg = [2 2 10];
cfg2.IMU.gyroBiasDps = [0.5 -0.3 0.2];
cfg2.IMU.accelBiasMg = [20 -15 10];
cfg2.GNSS.posSigmaH = 2;  cfg2.GNSS.posSigmaV = 4;
eng2 = SimEngine(cfg2);
eng2.runToEnd();
res2 = eng2.results();
calBg = rad2deg(res2.calBg(:, end));
trueBias = [0.5; -0.3; 0.2];   % injected gyro bias (deg/s)
bgErr = max(abs(calBg - trueBias));
assert(bgErr < 0.25, ...
    sprintf(['exp2: gyro bias did not converge to true [%.1f %.1f %.1f] ' ...
    '(max err %.3f): got [%.3f %.3f %.3f]'], trueBias, bgErr, calBg));
fprintf('  golden exp2: calBg = [%.3f %.3f %.3f] deg/s (true [%.1f %.1f %.1f], err %.3f)\n', ...
    calBg, trueBias, bgErr);
end
