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

disp('  utils: conversions OK');
