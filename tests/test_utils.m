%TEST_UTILS Quaternion/Euler/DCM/LLA conversion round-trips.
tol = 1e-9;

for k = 1:50
    e = [ (rand-0.5)*2.9; (rand-0.5)*1.4; (rand-0.5)*2*pi ];  % avoid gimbal lock
    q = eul2quat(e);
    assert(abs(norm(q) - 1) < tol, 'quaternion not normalized');
    e2 = quat2eul(q);
    assert(max(abs(wrapPi(e2 - e))) < 1e-8, 'euler roundtrip failed');
    C = eul2dcm(e);
    e3 = dcm2eul(C);
    assert(max(abs(wrapPi(dcm2eul(quat2dcm(dcm2quat(C))) - e3))) < 1e-9, 'dcm/quat roundtrip');
    C2 = quat2dcm(eul2quat(dcm2eul(C)));
    assert(max(abs(C(:) - C2(:))) < 1e-9, 'identity');
end

% specific known values
C = eul2dcm([0.1; -0.2; 0.3]);
assert(abs(C(3,1) - -sin(-0.2)) < 1e-12, 'DCM(3,1)');

% skew product
a = rand(3,1); b = rand(3,1);
assert(max(abs(skew(a)*b - cross(a,b))) < 1e-12, 'skew = cross');

% lla<->ned roundtrip
lla0 = [50.478; 12.365; 430];
ned = [1234.5; -678.9; -150];
lla = ned2lla(ned, lla0);
ned2 = lla2ned(lla, lla0);
assert(max(abs(ned - ned2)) < 1e-6, 'lla2ned roundtrip');

% eulRates2body sanity: pure yaw rate about level attitude
w = eulRates2body([0; 0; 0.4], [0; 0; 1.0]);
assert(max(abs(w - [0; 0; 1])) < 1e-12, 'pure yaw rate');

% set/get by path
s = struct('A', struct('b', [1 2 3]));
s = setByPath(s, 'A.b(2)', 99);
assert(getByPath(s, 'A.b(2)') == 99, 'set/getByPath');

% qScale must scale every process-noise density, including bias RW terms.
c1 = defaultConfig(); c1.Fusion.qScale = 1;
c2 = c1; c2.Fusion.qScale = 10;
e1 = LooselyCoupledEKF(); e1.initState(c1); e1.P(:) = 0;
e2 = LooselyCoupledEKF(); e2.initState(c2); e2.P(:) = 0;
e1.predict(eye(3), zeros(3,1), 1, c1);
e2.predict(eye(3), zeros(3,1), 1, c2);
assert(abs(e2.P(10,10) / e1.P(10,10) - 100) < 1e-10, 'qScale ignored gyro-bias RW');
assert(abs(e2.P(13,13) / e1.P(13,13) - 100) < 1e-10, 'qScale ignored accel-bias RW');

% Error-state attitude feedback must leave the cached DCM orthonormal and
% exactly synchronized with its quaternion representation.
mech = INSMechanization();
mech.reset(zeros(3,1), zeros(3,1), zeros(3,1), c1);
mech.correctState(zeros(3,1), zeros(3,1), [0.1; -0.07; 0.04]);
assert(norm(mech.C' * mech.C - eye(3), 'fro') < 1e-12, ...
    'attitude feedback left a non-orthogonal DCM');
assert(norm(mech.C - quat2dcm(mech.q), 'fro') < 1e-12, ...
    'cached DCM and quaternion disagree after attitude feedback');

% Reinitializing aiding must not expose an innovation from a previous run.
fresh = LooselyCoupledEKF(); fresh.initState(c1);
fresh.updatePos([3; 4; 5], eye(3));
assert(norm(fresh.lastInnov) > 0 && fresh.lastNIS > 0, 'EKF test setup produced no innovation');
fresh.initState(c1);
assert(norm(fresh.lastInnov) == 0 && fresh.lastNIS == 0, ...
    'EKF reinitialization retained stale innovation diagnostics');

disp('  utils: conversions, process noise, attitude feedback and EKF reset OK');
