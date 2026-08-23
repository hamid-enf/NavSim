%TEST_GNSS_DROPOUT Fused solution coasts through GNSS outages and recovers.
cfg = defaultConfig();
cfg.Sim.duration = 120;
cfg.Traj.type = 'Circle';
cfg.Fusion.mode = 'loose';
cfg.Align.enabled = true; cfg.Align.duration = 5;
cfg.GNSS.useDropout = true;
cfg.GNSS.dropoutText = '40 70';
cfg.IMU.gyroBiasDps = [0.1 -0.05 0.05];
cfg.IMU.accelBiasMg = [5 -3 2];

eng = SimEngine(cfg);
eng.runToEnd();
res = eng.results();

inOut = find(res.t >= 55 & res.t <= 69);   % deep inside outage
post  = find(res.t >= 80);                  % after recovery window

% no measurements inside the outage
fl = res.gnssFlag(res.t > 41 & res.t < 69);
assert(all(isnan(fl)), 'GNSS measurement delivered during dropout');

% fused error inside outage stays well below an unaided INS reference
cfgI = cfg; cfgI.Fusion.mode = 'ins';
resI = ExperimentPresets.runHeadless(cfgI);
assert(mean(res.errPosFus(inOut)) < 0.6*mean(resI.errPosIns(inOut)), ...
    'fused solution not better than INS during outage');

% recovery after GNSS returns
assert(mean(res.errPosFus(post)) < 3*cfg.GNSS.posSigmaH, ...
    sprintf('no reconvergence after outage: %.2f m', mean(res.errPosFus(post))));
fprintf('  dropout: fused-in-outage %.2f m (INS %.2f m), post-recovery %.2f m\n', ...
    mean(res.errPosFus(inOut)), mean(resI.errPosIns(inOut)), mean(res.errPosFus(post)));
