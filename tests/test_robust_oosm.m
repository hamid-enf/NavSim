%TEST_ROBUST_OOSM NIS policies and fixed-lag delayed-state replay.

% Robust reject leaves both state and covariance untouched.
c=defaultConfig(); c.Fusion.robustMode='reject'; c.Fusion.nisGatePos=10;
k=LooselyCoupledEKF(); k.initState(c); P0=k.P; x0=k.x;
ok=k.updatePos([1e5;0;0],eye(3));
assert(~ok && norm(k.P-P0,'fro')==0 && norm(k.x-x0)==0 && k.rejectedCount==1, ...
    'reject-mode NIS gate modified the filter');

% Adaptive mode downweights a moderate innovation; its cap still rejects an
% extreme innovation.  Off mode intentionally retains legacy always-update behavior.
a=c; a.Fusion.robustMode='adaptive'; a.Fusion.nisGatePos=1;
a.Fusion.maxRInflation=100;
ka=LooselyCoupledEKF(); ka.initState(a);
ok=ka.updatePos([10;0;0],eye(3));
assert(ok && ka.lastRawNIS>ka.lastGate && ka.lastNIS<ka.lastRawNIS, ...
    'adaptive robust update did not inflate measurement covariance');
Pbefore=ka.P; ok=ka.updatePos([1e8;0;0],eye(3));
assert(~ok && norm(ka.P-Pbefore,'fro')==0, 'adaptive inflation cap did not reject');
o=c; o.Fusion.robustMode='off'; ko=LooselyCoupledEKF(); ko.initState(o);
assert(ko.updatePos([1e8;0;0],eye(3)), 'robust off mode rejected a measurement');

% A single delayed epoch corrected at its historical state and replayed must
% match the same epoch processed in sequence (deterministic, error-free run).
base=defaultConfig(); base.Sim.dt=0.05; base.Sim.duration=0.8;
base.Traj.type='Circle'; base.Traj.speed=20; base.Traj.radius=50;
base.Align.enabled=false; base.Fusion.mode='loose'; base.Fusion.robustMode='off';
base.Fusion.useOOSM=true; base.Fusion.oosmLag=1; base.GNSS.rate=1;
base.GNSS.useNoise=false; base.GNSS.useOutlier=false; base.GNSS.enableVel=true;
base.Fusion.useVel=true; base.INS.initPosErr=[20;-10;5];
for f={'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
       'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'}
    base.IMU.(f{1})=false;
end
now=base; now.GNSS.delay=0; en=SimEngine(now); en.runToEnd(); rn=en.results();
delayed=base; delayed.GNSS.delay=0.2; ed=SimEngine(delayed); ed.runToEnd(); rd=ed.results();
assert(ed.oosmApplied==1 && ed.oosmRejected==0 && ed.oosmTooOld==0, ...
    'fixed-lag engine did not apply the delayed epoch exactly once');
assert(norm(rd.fusP(:,end)-rn.fusP(:,end)) < 2e-8 && ...
       norm(rd.fusV(:,end)-rn.fusV(:,end)) < 2e-8 && ...
       norm(wrapPi(rd.fusE(:,end)-rn.fusE(:,end))) < 2e-10, ...
    'OOSM rewind/repropagation differs from in-sequence processing');
i=find(~isnan(rd.gnssTMeas),1,'first');
assert(abs(rd.t(i)-0.2)<1e-12 && abs(rd.gnssTMeas(i))<1e-12 && ...
       rd.gnssOosm(i)==1 && rd.gnssAccepted(i)==1, ...
    'delayed measurement epoch/status was not logged correctly');

% Samples outside the configured lag are classified separately from NIS rejects.
old=base; old.Sim.duration=0.6; old.GNSS.delay=0.4; old.Fusion.oosmLag=0.2;
eo=SimEngine(old); eo.runToEnd(); ro=eo.results();
assert(eo.oosmTooOld==1 && eo.oosmApplied==0 && any(ro.gnssFlag==4), ...
    'too-old OOSM was not classified separately');

% End-to-end outlier rejection reaches logger/UI-facing diagnostics.
rj=base; rj.Sim.duration=0.1; rj.GNSS.enableVel=false; rj.Fusion.useVel=false;
rj.GNSS.delay=0; rj.GNSS.useOutlier=true; rj.GNSS.outlierProb=1;
rj.GNSS.outlierMag=1e6; rj.Fusion.robustMode='reject';
er=SimEngine(rj); er.runToEnd(); rr=er.results();
assert(er.gnssRejected==1 && rr.gnssFlag(1)==3 && rr.gnssAccepted(1)==0 && ...
       rr.nis(1)>rj.Fusion.nisGatePos, 'engine did not expose robust NIS rejection');

fprintf('  robust/OOSM: reject/adaptive/off gates and fixed-lag replay OK\n');
