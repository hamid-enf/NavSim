%TEST_AIDING Barometric altitude aiding, ZUPT and correlated GNSS error.

% ---------- 1) GNSS Gauss-Markov correlated error: unit properties ----------
c = defaultConfig();
c.GNSS.useNoise = false;  c.GNSS.biasNed = [0 0 0];
c.GNSS.useOutlier = false;  c.GNSS.rate = 10;
tr.p = [0;0;0];  tr.v = [0;0;0];
tr.lla = [c.INS.refLat; c.INS.refLon; c.INS.refH];

g0 = GNSSModel();  g0.updateParams(c);  g0.reset();
[hasA, zA] = g0.update(0.0, tr);  [hasB, zB] = g0.update(0.1, tr);
assert(hasA && hasB && max(abs(zA.p - tr.p)) == 0 && max(abs(zB.p - tr.p)) == 0, ...
    'with GM off, noise-free GNSS must measure truth exactly');

c.GNSS.useGmNoise = true;  c.GNSS.gmTau = 1e9;  c.GNSS.gmSigma = 5;
g1 = GNSSModel();  g1.updateParams(c);  g1.reset();
[~, zC] = g1.update(0.0, tr);  [~, zD] = g1.update(0.1, tr);
assert(norm(zC.p) > 0.5, 'GM state was not drawn from its stationary distribution');
assert(max(abs(zC.p - zD.p)) < 1e-3, ...
    'long-tau GM error must be quasi-constant across epochs');

% ---------- 2) GNSS velocity outliers ----------
c2 = defaultConfig();
c2.GNSS.enableVel = true;  c2.GNSS.useNoise = false;
c2.GNSS.useOutlier = true;  c2.GNSS.outlierProb = 1;
c2.GNSS.outlierMag = 0;  c2.GNSS.outlierVelSigma = 50;  c2.GNSS.rate = 10;
g2 = GNSSModel();  g2.updateParams(c2);  g2.reset();
errSum = 0;  n = 0;
for k = 0:29
    [has, zk] = g2.update(0.1*k, tr);
    if has && ~isempty(zk) && zk.hasVel
        errSum = errSum + norm(zk.v - tr.v);  n = n + 1;
    end
end
assert(n >= 25 && errSum/n > 15, ...
    'outlier velocity error was not injected (mean norm %.2g m/s)', errSum/max(n,1));
c2.GNSS.outlierVelSigma = 0;
g3 = GNSSModel();  g3.updateParams(c2);  g3.reset();
[~, zE] = g3.update(0.0, tr);
assert(norm(zE.v - tr.v) == 0, 'with outlierVelSigma=0 velocity must stay clean');

% ---------- 3) ZUPT: stationary platform, GNSS disabled ----------
c3 = defaultConfig();
c3.Traj.type = 'Straight';  c3.Traj.speed = 0;  c3.Sim.duration = 60;
c3.IMU.accelBiasMg = [10 -8 10];
c3.GNSS.enabled = false;  c3.Align.enabled = false;
c3.Fusion.mode = 'loose';  c3.Fusion.useZupt = true;
c3.Fusion.zuptHoldS = 0.5;  c3.Fusion.zuptSigma = 0.05;
e3 = SimEngine(c3);  e3.runToEnd();  r3 = e3.results();
assert(max(r3.errPosIns) > 40, ...
    sprintf('INS-only drift unexpectedly small: %.2g m', max(r3.errPosIns)));
assert(max(r3.errPosFus) < 8, ...
    sprintf('ZUPT failed to bound the error: %.3g m', max(r3.errPosFus)));
assert(max(r3.errVelFus) < 0.3, ...
    sprintf('ZUPT failed to pin velocity: %.3g m/s', max(r3.errVelFus)));

% ---------- 4) Baro aiding: climbing trajectory, GNSS disabled ----------
c4 = defaultConfig();
c4.Traj.type = 'Climb';  c4.Traj.speed = 10;  c4.Traj.climbRate = 3;
c4.Sim.duration = 60;
c4.IMU.accelBiasMg = [0 0 10];
c4.GNSS.enabled = false;  c4.Align.enabled = false;
c4.Fusion.mode = 'loose';
c4.Baro.enabled = true;  c4.Baro.sigma = 1;  c4.Baro.rate = 10;
e4 = SimEngine(c4);  e4.runToEnd();  r4 = e4.results();
insDownEnd = abs(r4.insP(3,end) - r4.truthP(3,end));
fusDownMax = max(abs(r4.fusP(3,:) - r4.truthP(3,:)));
assert(insDownEnd > 40, ...
    sprintf('vertical INS drift unexpectedly small: %.2g m', insDownEnd));
assert(fusDownMax < 8, ...
    sprintf('baro aiding failed to bound vertical error: %.3g m', fusDownMax));

fprintf('  aiding: GM GNSS + vel outlier OK; ZUPT pos %.2f m (INS %.0f m); baro down %.2f m (INS %.0f m)\n', ...
    max(r3.errPosFus), max(r3.errPosIns), fusDownMax, insDownEnd);
