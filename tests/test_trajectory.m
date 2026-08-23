%TEST_TRAJECTORY Exercise every trajectory and heading/alignment edge cases.
cfg = defaultConfig();
cfg.Sim.duration = 20;
types = TrajectoryLibrary.list();
for i = 1:numel(types)
    p = cfg.Traj; p.durationVal = cfg.Sim.duration;
    p.type = types{i};
    T = TrajectoryLibrary.make(types{i}, p);
    for t = [0 0.1 3.7 20]
        q = T.fh(t);
        vals = [q.p(:); q.v(:); q.a(:); q.eul(:); q.eulDot(:)];
        assert(all(isfinite(vals)), sprintf('%s produced non-finite truth at t=%g', types{i}, t));
        assert(all(size(q.p) == [3 1]) && all(size(q.v) == [3 1]), ...
            sprintf('%s did not return column vectors', types{i}));
    end
end

% heading0 is the initial horizontal heading for curved trajectories too.
for type = {'Circle','FigureEight','Combined3D'}
    p = cfg.Traj; p.heading0 = -37; p.durationVal = cfg.Sim.duration;
    T = TrajectoryLibrary.make(type{1}, p);
    q = T.fh(0);
    assert(abs(wrapPi(q.eul(3) - deg2rad(p.heading0))) < 1e-10, ...
        sprintf('%s ignores heading0 (got %.6f deg)', type{1}, rad2deg(q.eul(3))));
end

% Starting from rest while accelerating is not a valid static-levelling case.
p = cfg.Traj; p.speed = 0; p.accel = 2;
T = TrajectoryLibrary.make('Acceleration', p);
a = Alignment(); a.reset(cfg, T.fh(0));
assert(~a.isStatic, 'accelerating trajectory was incorrectly classified as static');

% A slowly moving but rotating platform is not static alignment either.
p = cfg.Traj; p.speed = 0.5; p.radius = 10;
T = TrajectoryLibrary.make('Circle', p);
a.reset(cfg, T.fh(0));
assert(~a.isStatic, 'rotating low-speed trajectory was incorrectly classified as static');

% Regression: the old Descent ground clamp jumped vD to zero without an
% acceleration impulse and made a perfect IMU diverge dramatically.
dc = defaultConfig();
dc.Sim.duration = 12; dc.Traj.type = 'Descent';
dc.Traj.alt0 = 10; dc.Traj.climbRate = 1;
dc.Align.enabled = false; dc.Fusion.mode = 'ins'; dc.GNSS.enabled = false;
for f = {'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
          'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'}
    dc.IMU.(f{1}) = false;
end
de = SimEngine(dc); de.runToEnd(); dr = de.results();
assert(max(dr.errPosIns) < 0.01 && max(dr.errVelIns) < 0.01, ...
    sprintf('perfect-IMU Descent is inconsistent: pos %.3g m, vel %.3g m/s', ...
    max(dr.errPosIns), max(dr.errVelIns)));

% Turn entry must be smooth enough that it does not inject an attitude
% impulse into an otherwise perfect INS.
tc = dc; tc.Sim.duration = 20; tc.Traj.type = 'Turn';
te = SimEngine(tc); te.runToEnd(); tr = te.results();
assert(max(tr.errPosIns) < 0.2 && max(tr.errVelIns) < 0.05 && ...
       rad2deg(max(tr.errAttIns)) < 0.3, ...
    sprintf('Turn entry is discontinuous: pos %.3g m, vel %.3g m/s, att %.3g deg', ...
    max(tr.errPosIns), max(tr.errVelIns), rad2deg(max(tr.errAttIns))));

% Invalid headless settings fail early instead of hanging/dividing by zero.
bad = cfg; bad.Sim.dt = 0;
caught = false;
try
    SimEngine(bad);
catch ME
    caught = strcmp(ME.identifier, 'NavSim:InvalidConfig');
end
assert(caught, 'zero Sim.dt was not rejected by config validation');

bad = cfg; bad.Sim.dt = 0.05; bad.GNSS.enabled = true; bad.GNSS.rate = 50;
caught = false;
try
    SimEngine(bad);
catch ME
    caught = strcmp(ME.identifier, 'NavSim:InvalidConfig');
end
assert(caught, 'GNSS rate above simulation polling rate was silently accepted');

% Failed reconfiguration must leave an existing engine usable.
good = defaultConfig(); good.Align.enabled = false; survivor = SimEngine(good);
bad = good; bad.Traj.type = 'UserDefined'; bad.Traj.userExpr = '[1; 2]';
caught = false;
try
    survivor.configure(bad);
catch ME
    caught = strcmp(ME.identifier, 'TrajectoryLibrary:badUser');
end
assert(caught && strcmp(survivor.cfg.Traj.type, good.Traj.type), ...
    'failed configure partially mutated the existing engine');
survivor.step();
assert(survivor.k == 1, 'engine was unusable after rejected reconfiguration');

fprintf('  trajectories: %d finite; heading/dynamics/Descent/config transactions OK\n', ...
    numel(types));
