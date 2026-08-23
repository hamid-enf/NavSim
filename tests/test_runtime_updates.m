%TEST_RUNTIME_UPDATES Runtime GNSS scheduling and fusion-mode transitions.
cfg = defaultConfig();
cfg.GNSS.useNoise = false; cfg.GNSS.useOutlier = false;
cfg.GNSS.useDropout = false; cfg.GNSS.rate = 1; cfg.GNSS.delay = 0;
truth = struct('p', zeros(3,1), 'v', zeros(3,1));
g = GNSSModel(); g.updateParams(cfg); g.reset();
[has0, ~, ~] = g.update(0, truth);
assert(has0, 'GNSS did not emit its initial epoch');

% Increasing rate at t=.1 should schedule from the change time, rather than
% waiting for the stale 1-Hz epoch at t=1.
cfg.GNSS.rate = 10;
g.updateParams(cfg, 0.1);
[hasEarly, ~, ~] = g.update(0.19, truth);
[hasNew, ~, ~] = g.update(0.2, truth);
assert(~hasEarly && hasNew, 'runtime GNSS rate change did not resynchronize epochs');

% Disabling GNSS clears delayed measurements so stale data cannot appear
% after the receiver is enabled again.
cfg.GNSS.delay = 1;
g2 = GNSSModel(); g2.updateParams(cfg); g2.reset();
[hasDelayed, ~, ~] = g2.update(0, truth);
assert(~hasDelayed && ~isempty(g2.queue), 'delayed GNSS measurement was not queued');
cfg.GNSS.enabled = false; g2.updateParams(cfg, 0.1);
assert(isempty(g2.queue), 'disabling GNSS retained stale delayed measurements');
cfg.GNSS.enabled = true; cfg.GNSS.delay = 0; g2.updateParams(cfg, 0.2);
[hasEnabled, ~, ~] = g2.update(0.2, truth);
assert(hasEnabled, 'GNSS did not reacquire immediately after re-enable');

% Malformed dropout text must be reported, not silently ignored.
bad = cfg; bad.GNSS.dropoutText = '40 nope 70';
caught = false;
try
    g2.updateParams(bad, 0.3);
catch ME
    caught = strcmp(ME.identifier, 'NavSim:InvalidDropoutWindows');
end
assert(caught, 'malformed dropout window was silently accepted');

% The master bias toggles must also suppress configured/accumulated bias RW.
rw = defaultConfig();
rw.IMU.useGyroBias = false; rw.IMU.gyroBiasRW = 1;
rw.IMU.useAccelBias = false; rw.IMU.accelBiasRW = 1;
im = IMUModel(); im.updateParams(rw); im.reset();
[~, ~, dbg] = im.measure(zeros(3,1), zeros(3,1), 1);
assert(norm(dbg.bg) == 0 && norm(dbg.ba) == 0, ...
    'disabled bias master toggle still injected bias random walk');

% Runtime switch to INS-only drops stale filter/calibration state and
% switching back starts with a fresh covariance.
c3 = defaultConfig(); c3.Align.enabled = false; c3.Sim.duration = 1;
p0Before = c3.Fusion.p0pos;
e = SimEngine(c3); e.step();
e.calibBg = [1;2;3]; e.calibBa = [4;5;6];
c3.Sim.duration = 0.5;  % pending structural edits must not leak into runtime update
c3.Sim.dt = 0.05;       % incompatible with 50-Hz GNSS if applied prematurely
c3.GNSS.rate = 50;
c3.Fusion.p0pos = 99;
c3.Fusion.mode = 'ins'; e.applyRuntime(c3);
assert(e.cfg.Sim.duration == 1 && e.cfg.Sim.dt == 0.01 && ...
       e.cfg.Fusion.p0pos == p0Before && e.cfg.GNSS.rate == 50, ...
    'runtime merge leaked structural/P0 config or rejected a valid merged rate');
assert(~e.ekf.initialized, 'EKF remained initialized in INS-only mode');
assert(norm(e.calibBg) == 0 && norm(e.calibBa) == 0, 'INS-only mode retained filter calibration');
assert(norm(e.ins.p - e.insPure.p) < eps && norm(e.ins.v - e.insPure.v) < eps, ...
    'INS-only nominal state did not switch to the unaided solution');
c3.Fusion.mode = 'loose'; e.applyRuntime(c3);
assert(e.ekf.initialized, 'EKF was not freshly initialized when aiding resumed');

fprintf('  runtime: GNSS reschedule/re-enable and Fusion mode transitions OK\n');
