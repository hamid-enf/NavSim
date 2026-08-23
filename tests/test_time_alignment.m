%TEST_TIME_ALIGNMENT Regression tests for engine timing and live snapshots.
cfg = defaultConfig();
cfg.Sim.duration = 2;
cfg.Sim.dt = 0.01;
cfg.Traj.type = 'Circle';
cfg.Traj.speed = 20; cfg.Traj.radius = 50;
cfg.GNSS.enabled = false;
cfg.Fusion.mode = 'ins';
cfg.Align.enabled = true; cfg.Align.duration = 1;
cfg.Align.applyUserErr = false;
cfg.Align.coarseMovingSigmaDeg = 0;
for f = {'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
          'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'}
    cfg.IMU.(f{1}) = false;
end
eng = SimEngine(cfg);
eng.runToEnd();
r = eng.results();
firstNav = find(~isnan(r.insP(1,:)), 1, 'first');
assert(~isempty(firstNav), 'no navigation samples after alignment');
assert(abs(r.t(firstNav) - cfg.Align.duration) < 1e-8, ...
    sprintf('first nav sample is at %.12g instead of alignment boundary %.12g', ...
    r.t(firstNav), cfg.Align.duration));
assert(r.errPosIns(firstNav) < 1e-8, ...
    sprintf('post-alignment state is time-shifted by one step (%.6g m)', r.errPosIns(firstNav)));
assert(rad2deg(r.errAttIns(firstNav)) < 1e-7, ...
    sprintf('post-alignment attitude is time-shifted (%.6g deg)', rad2deg(r.errAttIns(firstNav))));

% Snapshot fields must all describe the logged sample at t, not a mixture
% of pre- and post-propagation states.
c2 = cfg;
c2.Align.enabled = false; c2.Sim.duration = 0.025;
e2 = SimEngine(c2);
e2.step();
s = e2.getSnapshot();
d = e2.log.slice();
assert(abs(s.t - d.t(end)) < eps, 'snapshot timestamp does not match log row');
assert(norm(s.insState.p - d.insP(:,end)) < eps, 'snapshot INS is one step ahead of log/Truth');
assert(abs(s.engineTime - c2.Sim.dt) < 1e-12, 'snapshot engineTime is incorrect');
e2.runToEnd();
d = e2.log.slice();
assert(abs(e2.t - c2.Sim.duration) < 1e-12, 'engine integrated past requested duration');
assert(abs(sum(d.dt) - c2.Sim.duration) < 1e-12, 'final integration interval was not clamped');

% Truth and INS must use the same altitude-dependent gravity model.
c3 = defaultConfig();
c3.Sim.duration = 60; c3.Traj.type = 'Straight'; c3.Traj.speed = 0;
c3.Traj.alt0 = 100; c3.GNSS.enabled = false; c3.Fusion.mode = 'ins';
c3.Align.enabled = false; c3.Align.applyUserErr = false;
for f = {'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
          'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'}
    c3.IMU.(f{1}) = false;
end
e3 = SimEngine(c3); e3.runToEnd(); r3 = e3.results();
assert(max(r3.errPosIns) < 1e-7, ...
    sprintf('gravity mismatch causes perfect-IMU drift: %.6g m', max(r3.errPosIns)));

fprintf('  timing: first nav exactly at %.2f s; snapshot aligned; gravity drift %.3g m\n', ...
    r.t(firstNav), max(r3.errPosIns));
