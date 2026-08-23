%TEST_PERFECT_MATCH Zero-error sanity:
%  bias = 0, noise = 0, GNSS error = 0  =>  navigation ~= truth.
cfg = defaultConfig();
cfg.Sim.duration = 60;
cfg.Sim.dt = 0.01;
cfg.Traj.type = 'Circle';
cfg.Traj.speed = 15;  cfg.Traj.radius = 200;
% switch off every error source
I = 'IMU.'; G = 'GNSS.';
f = {'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
     'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'};
for i = 1:numel(f), cfg = setByPath(cfg, [I f{i}], false); end
cfg.GNSS.useNoise = false;  cfg.GNSS.useOutlier = false;
cfg.GNSS.useDropout = false; cfg.GNSS.biasNed = [0 0 0];
cfg.Align.applyUserErr = false;  cfg.Align.enabled = false;
cfg.Fusion.mode = 'loose';

eng = SimEngine(cfg);
eng.runToEnd();
res = eng.results();

assert(res.n > 5000, 'not enough samples');
assert(max(res.errPosFus) < 0.10, sprintf('pos error too large: %.4f m', max(res.errPosFus)));
assert(max(res.errVelFus) < 0.05, sprintf('vel error too large: %.4f m/s', max(res.errVelFus)));
assert(max(res.errAttFus) < deg2rad(0.05), sprintf('att error too large: %.4f deg', ...
    rad2deg(max(res.errAttFus))));
fprintf('  perfect match: max pos err = %.4f m, max att err = %.5f deg\n', ...
    max(res.errPosFus), rad2deg(max(res.errAttFus)));
