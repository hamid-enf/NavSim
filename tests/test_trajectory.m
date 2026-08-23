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

% Invalid headless settings fail early instead of hanging/dividing by zero.
bad = cfg; bad.Sim.dt = 0;
caught = false;
try
    SimEngine(bad);
catch ME
    caught = strcmp(ME.identifier, 'NavSim:InvalidConfig');
end
assert(caught, 'zero Sim.dt was not rejected by config validation');

fprintf('  trajectories: %d types finite; curved heading0 and dynamic alignment classification OK\n', ...
    numel(types));
