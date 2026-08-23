%TEST_ALIGNMENT Coarse levelling converges to true roll/pitch while static.
cfg = defaultConfig();
cfg.Traj.type = 'Straight';
cfg.Traj.speed = 0;                 % static platform
cfg.Sim.duration = 30;
cfg.Align.enabled = true;
cfg.Align.duration = 25;
cfg.Align.coarseLevel = true;
cfg.Align.applyUserErr = false;
cfg.Align.magHeadingSigmaDeg = 0.5;
% zero biases so levelling accuracy is limited by noise only
cfg.IMU.useGyroBias = false; cfg.IMU.useAccelBias = false;

eng = SimEngine(cfg);
% mid-alignment error should exceed late-alignment error (convergence)
while eng.t < cfg.Align.duration
    eng.step();
end

res = eng.results();
am = ~isnan(res.alignEst(1,:));
assert(any(am), 'no alignment estimates logged');
idx = find(am);
early = idx(round(0.1*numel(idx)));
late  = idx(end);
acc = sqrt(res.accM(1,:).^2); %#ok<NASGU>
errE = rad2deg(norm(wrapPi(res.alignEst(1:2,early) - res.truthE(1:2,early))));
errL = rad2deg(norm(wrapPi(res.alignEst(1:2,late)  - res.truthE(1:2,late))));
assert(errL < 0.2, sprintf('levelling error too large: %.3f deg', errL));
assert(errL <= errE + 1e-9, sprintf('no convergence: early %.3f deg late %.3f deg', errE, errL));
fprintf('  alignment: level err early %.3f deg -> late %.3f deg\n', errE, errL);
