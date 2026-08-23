%TEST_VARIABLE_DT INS must stay consistent under variable dt (timing error).
base = defaultConfig();
base.Traj.type = 'Combined3D';
base.Sim.duration = 60;
base.Align.enabled = false;
base.Fusion.mode = 'ins';          % isolate INS integration behaviour
for f = {'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
          'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'}
    base.IMU.(f{1}) = false;
end

c1 = base;  c1.Sim.variableDt = 'off';
c2 = base;  c2.Sim.variableDt = 'jitter';  c2.Sim.dtJitter = 0.6;
c3 = base;  c3.Sim.variableDt = 'tworate';

r1 = ExperimentPresets.runHeadless(c1);
r2 = ExperimentPresets.runHeadless(c2);
r3 = ExperimentPresets.runHeadless(c3);

% final INS positions must agree (same physical truth, error-free IMU)
d12 = norm(r1.insP(:,end) - r2.insP(:,end));
d13 = norm(r1.insP(:,end) - r3.insP(:,end));
assert(d12 < 0.5, sprintf('jitter vs const dt mismatch: %.3f m', d12));
assert(d13 < 0.5, sprintf('tworate vs const dt mismatch: %.3f m', d13));
% dt statistics actually differ
assert(std(r2.dt) > 10*std(r1.dt), 'jitter not active');
fprintf('  variable dt: const-vs-jitter %.3f m, const-vs-tworate %.3f m\n', d12, d13);
