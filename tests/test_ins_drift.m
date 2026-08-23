%TEST_INS_DRIFT INS-only error growth with gyro bias:
%  with no GNSS aiding the position error must grow over time.
cfg = defaultConfig();
cfg.Sim.duration = 120;
cfg.Traj.type = 'Circle';
cfg.Fusion.mode = 'ins';              % INS only
cfg.Align.enabled = false;
cfg.Align.applyUserErr = false;
% isolate gyro bias
for f = {'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
          'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'}
    cfg.IMU.(f{1}) = false;
end
cfg.IMU.useGyroBias = true;
cfg.IMU.gyroBiasDps = [0.5 -0.3 0.2];

eng = SimEngine(cfg);
eng.runToEnd();
res = eng.results();

e = res.errPosIns;
q1 = mean(e(round(0.1*res.n):round(0.2*res.n)));
q4 = mean(e(round(0.8*res.n):end));
assert(q4 > 3*q1, sprintf('drift not growing: early %.2f m, late %.2f m', q1, q4));
fprintf('  INS drift: early %.2f m -> late %.2f m (growth x%.1f)\n', q1, q4, q4/q1);

% accel bias should produce roughly quadratic position error growth
cfg2 = cfg;
cfg2.IMU.useGyroBias = false;
cfg2.IMU.useAccelBias = true;
cfg2.IMU.accelBiasMg = [10 0 0];
cfg2.Traj.type = 'Straight'; cfg2.Traj.speed = 0;   % static: pure integration
eng2 = SimEngine(cfg2);
eng2.runToEnd();
res2 = eng2.results();
b = 10e-3 * 9.80665;
expected = 0.5 * b * res2.t(end)^2;    % 0.5*b*t^2 along one axis
actual = res2.errPosIns(end);
assert(abs(actual - expected) / expected < 0.05, ...
    sprintf('accel-bias drift: expected ~%.1f m, got %.1f m', expected, actual));
fprintf('  accel-bias drift matches 1/2*b*t^2: %.1f m vs theory %.1f m\n', actual, expected);
