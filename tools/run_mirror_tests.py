#!/usr/bin/env python3
"""Mirror of the MATLAB numerical suite against the Python mirror engine."""
import copy
import sys
import numpy as np
from navsim_mirror import *

results = []
def check(name, fn):
    try:
        fn()
        results.append((name, True, ""))
        print(f"  [PASS] {name}")
    except Exception as e:
        results.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"  [FAIL] {name}: {type(e).__name__}: {e}")

def no_imu_errors(cfg):
    for f in ['useGyroBias','useGyroNoise','useGyroSF','useGyroMis',
              'useAccelBias','useAccelNoise','useAccelSF','useAccelMis']:
        cfg['IMU'][f] = False
    return cfg

def t_utils():
    rng = np.random.default_rng(123)
    for _ in range(100):
        e = np.array([(rng.random()-.5)*2.9, (rng.random()-.5)*1.4,
                      (rng.random()-.5)*2*np.pi])
        q = eul2quat(e)
        assert abs(np.linalg.norm(q)-1) < 1e-12
        assert np.max(np.abs(wrapPi(quat2eul(q)-e))) < 1e-10
        C = eul2dcm(e)
        assert np.max(np.abs(C-quat2dcm(dcm2quat(C)))) < 1e-10
    a=rng.random(3); b=rng.random(3)
    assert np.max(np.abs(skew(a)@b-np.cross(a,b))) < 1e-12
    p=default_config()['Traj']; p['heading0']=-37
    for tp in ('Circle','FigureEight','Combined3D'):
        tr=make_traj(tp,p); q=tr(0)
        assert abs(wrapPi(q['eul'][2]-np.radians(p['heading0']))) < 1e-10

    # Low-speed turns must retain heading rate for static-alignment gating.
    slow=default_config()['Traj']; slow['speed']=0.5; slow['radius']=10
    slow_truth=make_traj('Circle',slow)(0)
    align=Align(default_config(),slow_truth,np.random.default_rng(1))
    assert not align.isStatic, "rotating low-speed trajectory classified as static"

    c1=default_config(); c2=copy.deepcopy(c1); c2['Fusion']['qScale']=10
    e1=EKF(); e1.initState(c1); e1.P[:]=0; e1.predict(np.eye(3),np.zeros(3),1)
    e2=EKF(); e2.initState(c2); e2.P[:]=0; e2.predict(np.eye(3),np.zeros(3),1)
    assert abs(e2.P[9,9]/e1.P[9,9]-100)<1e-10, "qScale ignored gyro-bias RW"
    assert abs(e2.P[12,12]/e1.P[12,12]-100)<1e-10, "qScale ignored accel-bias RW"

    mech=INS()
    mech.correct(np.zeros(3),np.zeros(3),np.array([0.1,-0.07,0.04]))
    assert np.linalg.norm(mech.C.T@mech.C-np.eye(3))<1e-12
    assert np.linalg.norm(mech.C-quat2dcm(mech.q))<1e-12

    rw=default_config(); rw['IMU']['useGyroBias']=False; rw['IMU']['gyroBiasRW']=1
    rw['IMU']['useAccelBias']=False; rw['IMU']['accelBiasRW']=1
    im=IMU(rw); _,_,dbg=im.measure(np.zeros(3),np.zeros(3),1)
    assert np.linalg.norm(dbg['bg'])==0 and np.linalg.norm(dbg['ba'])==0
    print("      utils: conversions, low-speed turn, qScale, DCM feedback and bias toggles OK")

def t_perfect():
    cfg = default_config()
    cfg['Sim']['duration']=60; cfg['Sim']['dt']=0.01
    cfg['Traj']['type']='Circle'; cfg['Traj']['speed']=15; cfg['Traj']['radius']=200
    no_imu_errors(cfg)
    cfg['GNSS']['useNoise']=False; cfg['GNSS']['useOutlier']=False; cfg['GNSS']['useDropout']=False
    cfg['Align']['applyUserErr']=False; cfg['Align']['enabled']=False
    cfg['Fusion']['mode']='loose'
    res = Engine(cfg); res.run(); d = res.results()
    mp = d['errPosFus'].max(); ma = np.degrees(d['errAttFus']).max(); mv=d['errVelFus'].max()
    assert d['n']>5000, f"not enough samples {d['n']}"
    assert mp < 0.10, f"pos {mp:.4f} m"
    assert mv < 0.05, f"vel {mv:.4f} m/s"
    assert ma < 0.05, f"att {ma:.5f} deg"
    print(f"      perfect: maxPos={mp:.4f} m  maxVel={mv:.5f} m/s  maxAtt={ma:.5f} deg")

def t_drift():
    cfg = default_config()
    cfg['Sim']['duration']=120; cfg['Traj']['type']='Circle'
    cfg['Fusion']['mode']='ins'; cfg['Align']['enabled']=False; cfg['Align']['applyUserErr']=False
    no_imu_errors(cfg)
    cfg['IMU']['useGyroBias']=True; cfg['IMU']['gyroBiasDps']=[0.5,-0.3,0.2]
    d = Engine(cfg); d.run(); r = d.results()
    e=r['errPosIns']; n=r['n']
    q1=e[int(0.1*n):int(0.2*n)].mean(); q4=e[int(0.8*n):].mean()
    assert q4 > 3*q1, f"gyro drift ratio {q4/q1:.2f}"
    cfg2 = default_config()
    cfg2['Sim']['duration']=120; cfg2['Fusion']['mode']='ins'; cfg2['Align']['enabled']=False
    no_imu_errors(cfg2)
    cfg2['IMU']['useAccelBias']=True; cfg2['IMU']['accelBiasMg']=[10,0,0]
    cfg2['Traj']['type']='Straight'; cfg2['Traj']['speed']=0
    d2=Engine(cfg2); d2.run(); r2=d2.results()
    b=10e-3*9.80665; expected=0.5*b*r2['t'][-1]**2; actual=r2['errPosIns'][-1]
    assert abs(actual-expected)/expected < 0.05, f"accel drift {actual:.1f} vs {expected:.1f}"
    print(f"      drift: gyro growth x{q4/q1:.1f}; accel drift {actual:.1f} m vs theory {expected:.1f} m")

def t_ekf():
    cfg = default_config()
    cfg['Sim']['duration']=120; cfg['Traj']['type']='FigureEight'
    cfg['Fusion']['mode']='loose'
    cfg['Align']['enabled']=True; cfg['Align']['duration']=5
    cfg['Align']['applyUserErr']=True; cfg['Align']['userErrDeg']=[2,2,10]
    cfg['IMU']['gyroBiasDps']=[0.5,-0.3,0.2]; cfg['IMU']['accelBiasMg']=[20,-15,10]
    cfg['GNSS']['posSigmaH']=2; cfg['GNSS']['posSigmaV']=4
    d=Engine(cfg); d.run(); r=d.results()
    sl = r['t'] > r['t'][-1]-20
    rmsPos=float(np.sqrt((r['errPosFus'][sl]**2).mean()))
    rmsAtt=float(np.degrees(np.sqrt((r['errAttFus'][sl]**2).mean())))
    assert rmsPos < 3*cfg['GNSS']['posSigmaH'], f"rms pos {rmsPos:.2f}"
    valid = (~np.isnan(r['errAttFus'])) & (r['t'] > cfg['Align']['duration'])
    ia = int(np.argmax(valid))
    ratio = float(r['errAttFus'][-1]/max(r['errAttFus'][ia],1e-12))
    assert ratio<0.25, f"att ratio {ratio:.2f}"
    assert rmsAtt < 2.0, f"rms att {rmsAtt:.3f} deg"
    bg=np.degrees(r['calBg'][:,-1])
    assert abs(bg[0]-0.5)<0.15 and abs(bg[1]+0.3)<0.15, f"bg est {bg}"
    sig=r['sigP'][0,sl]; errN=np.abs(r['fusP'][0,sl]-r['truthP'][0,sl])
    fi=float((errN<3*sig).mean())
    assert fi>0.90, f"3sigma frac {fi:.2f}"
    print(f"      ekf: rmsPos={rmsPos:.2f} m  rmsAtt={rmsAtt:.3f} deg  bgEst={np.round(bg,3)} deg/s  in3sig={fi:.0%}")

def t_align():
    cfg = default_config()
    cfg['Traj']['type']='Straight'; cfg['Traj']['speed']=0
    cfg['Sim']['duration']=30
    cfg['Align']['enabled']=True; cfg['Align']['duration']=25; cfg['Align']['coarseLevel']=True
    cfg['Align']['applyUserErr']=False; cfg['Align']['magHeadingSigmaDeg']=0.5
    cfg['IMU']['useGyroBias']=False; cfg['IMU']['useAccelBias']=False
    e=Engine(cfg)
    while e.t < cfg['Align']['duration']: e.step()
    r=e.results()
    am=~np.isnan(r['alignEst'][0])
    idx=np.where(am)[0]
    early=idx[int(0.1*len(idx))]; late=idx[-1]
    errE=float(np.degrees(np.linalg.norm(wrapPi(r['alignEst'][0:2,early]-r['truthE'][0:2,early]))))
    errL=float(np.degrees(np.linalg.norm(wrapPi(r['alignEst'][0:2,late]-r['truthE'][0:2,late]))))
    assert errL<0.2, f"level err {errL:.3f} deg"
    assert errL<=errE+1e-9, f"no convergence {errE}->{errL}"
    print(f"      align: {errE:.3f} deg -> {errL:.3f} deg")

def t_vdt():
    base=no_imu_errors(default_config())
    base['Traj']['type']='Combined3D'; base['Sim']['duration']=60
    base['Align']['enabled']=False; base['Fusion']['mode']='ins'
    c1c=copy.deepcopy(base); c2c=copy.deepcopy(base); c3c=copy.deepcopy(base)
    c2c['Sim']['variableDt']='jitter'; c2c['Sim']['dtJitter']=0.6
    c3c['Sim']['variableDt']='tworate'
    r1=Engine(c1c); r1.run(); r1=r1.results()
    r2=Engine(c2c); r2.run(); r2=r2.results()
    r3=Engine(c3c); r3.run(); r3=r3.results()
    d12=float(np.linalg.norm(r1['insP'][:,-1]-r2['insP'][:,-1]))
    d13=float(np.linalg.norm(r1['insP'][:,-1]-r3['insP'][:,-1]))
    assert d12<0.5, f"d12 {d12:.3f}"
    assert d13<0.5, f"d13 {d13:.3f}"
    assert r2['dt'].std() > 10*max(r1['dt'].std(),1e-15), "jitter inactive"
    print(f"      vdt: d12={d12:.3f} m  d13={d13:.3f} m")

def t_dropout():
    cfg = default_config()
    cfg['Sim']['duration']=120; cfg['Traj']['type']='Circle'
    cfg['Fusion']['mode']='loose'
    cfg['Align']['enabled']=True; cfg['Align']['duration']=5
    cfg['GNSS']['useDropout']=True; cfg['GNSS']['dropoutText']='40 70'
    cfg['IMU']['gyroBiasDps']=[0.1,-0.05,0.05]; cfg['IMU']['accelBiasMg']=[5,-3,2]
    d=Engine(cfg); d.run(); r=d.results()
    inOut=(r['t']>=55)&(r['t']<=69); post=(r['t']>=80)
    fl=r['gnssFlag'][(r['t']>41)&(r['t']<69)]
    assert np.all(np.isnan(fl)), "GNSS delivered during dropout"
    cfgI=default_config()
    import copy; cfgI=copy.deepcopy(cfg); cfgI['Fusion']['mode']='ins'
    dI=Engine(cfgI); dI.run(); rI=dI.results()
    mf=float(r['errPosFus'][inOut].mean()); mi=float(rI['errPosIns'][inOut].mean())
    assert mf < 0.6*mi, f"fused {mf:.2f} vs INS {mi:.2f}"
    mp=float(r['errPosFus'][post].mean())
    assert mp < 3*cfg['GNSS']['posSigmaH'], f"post {mp:.2f}"
    print(f"      dropout: in-outage fused {mf:.2f} m (INS {mi:.2f} m), post {mp:.2f} m")

def t_time_alignment():
    cfg=no_imu_errors(default_config())
    cfg['Sim']['duration']=2; cfg['Traj']['type']='Circle'
    cfg['Traj']['speed']=20; cfg['Traj']['radius']=50
    cfg['GNSS']['enabled']=False; cfg['Fusion']['mode']='ins'
    cfg['Align']['enabled']=True; cfg['Align']['duration']=1
    cfg['Align']['applyUserErr']=False; cfg['Align']['coarseMovingSigmaDeg']=0
    e=Engine(cfg); e.run(); r=e.results()
    valid=np.flatnonzero(~np.isnan(r['insP'][0]))
    assert len(valid)>0, "no post-alignment samples"
    i=valid[0]
    assert abs(r['t'][i]-1)<1e-8, f"first nav time {r['t'][i]}"
    assert r['errPosIns'][i]<1e-8, f"one-step position lag {r['errPosIns'][i]}"
    assert np.degrees(r['errAttIns'][i])<1e-7, f"one-step attitude lag {np.degrees(r['errAttIns'][i])}"

    c=no_imu_errors(default_config())
    c['Sim']['duration']=60; c['Traj']['type']='Straight'; c['Traj']['speed']=0
    c['Traj']['alt0']=100; c['GNSS']['enabled']=False; c['Fusion']['mode']='ins'
    c['Align']['enabled']=False; c['Align']['applyUserErr']=False
    g=Engine(c); g.run(); rg=g.results()
    drift=float(np.nanmax(rg['errPosIns']))
    assert drift<1e-7, f"gravity mismatch drift {drift}"

    d=no_imu_errors(default_config())
    d['Sim']['duration']=12; d['Traj']['type']='Descent'; d['Traj']['alt0']=10
    d['Traj']['climbRate']=1; d['GNSS']['enabled']=False; d['Fusion']['mode']='ins'
    d['Align']['enabled']=False
    de=Engine(d); de.run(); dr=de.results()
    descent=float(np.nanmax(dr['errPosIns']))
    assert descent<0.01, f"perfect-IMU Descent inconsistency {descent}"

    turn=copy.deepcopy(d); turn['Sim']['duration']=20; turn['Traj']['type']='Turn'
    te=Engine(turn); te.run(); tr=te.results()
    turn_err=float(np.nanmax(tr['errPosIns']))
    turn_att=float(np.degrees(np.nanmax(tr['errAttIns'])))
    assert turn_err<0.2 and turn_att<0.3, f"Turn entry discontinuity {turn_err} m / {turn_att} deg"
    print(f"      timing: nav={r['t'][i]:.2f}s gravity={drift:.2g} descent={descent:.2g} turn={turn_err:.3g}m")


def t_aiding():
    import copy
    # ---------- GM correlated GNSS error: stationary statistics ----------
    c=default_config()
    c['GNSS'].update(useNoise=False, biasNed=[0,0,0], useOutlier=False,
                     rate=10.0, useGmNoise=True, gmSigma=2.0, gmTau=5.0)
    g=GNSS(c)
    truth=dict(p=np.zeros(3), v=np.zeros(3))
    errs=[]
    t=0.0
    # NOTE: samples are strongly autocorrelated (tau=5 s, Ts=0.1 s), so the
    # effective sample count is ~N*(1-rho)/(1+rho); keep N large for a tight
    # standard-deviation estimate (20000 epochs -> ~200 effective samples).
    for _ in range(20000):
        has,z,_=g.update(t,truth)
        if has: errs.append(z['p']-truth['p'])
        t+=0.1
    errs=np.array(errs)
    std=errs.std(axis=0)
    assert np.all(np.abs(std-2.0)/2.0 < 0.15), f"GM steady-state std off: {std}"
    a=errs[:-1].flatten(); b=errs[1:].flatten()
    rho=float(np.corrcoef(a,b)[0,1])   # lag-1 (0.1 s) correlation ~ exp(-0.1/5)
    assert abs(rho-np.exp(-0.1/5.0)) < 0.02, f"GM lag-1 autocorrelation off: {rho}"
    # GM off must reproduce exact noise-free measurements
    c2=default_config(); c2['GNSS'].update(useNoise=False, biasNed=[0,0,0], rate=10.0)
    g2=GNSS(c2)
    for tt in (0.0, 0.1):
        has,z,_=g2.update(tt,truth)
        assert has and np.max(np.abs(z['p']-truth['p']))==0.0

    # ---------- GNSS velocity outlier ----------
    c3=default_config()
    c3['GNSS'].update(enableVel=True, useNoise=False, useOutlier=True,
                      outlierProb=1.0, outlierMag=0.0, outlierVelSigma=50.0, rate=10.0)
    g3=GNSS(c3)
    en=[]; t=0.0
    for _ in range(30):
        has,z,_=g3.update(t,truth)
        if has and z['hasVel']: en.append(float(np.linalg.norm(z['v']-truth['v'])))
        t+=0.1
    assert len(en)==30 and np.mean(en)>15, f"velocity outlier missing (mean {np.mean(en):.2f})"

    # ---------- ZUPT: stationary, GNSS disabled ----------
    c4=default_config()
    c4['Traj'].update(type='Straight', speed=0.0)
    c4['Sim']['duration']=60.0
    c4['IMU']['accelBiasMg']=[10,-8,10]
    c4['GNSS']['enabled']=False
    c4['Align']['enabled']=False
    c4['Fusion'].update(useZupt=True, zuptHoldS=0.5, zuptSigma=0.05)
    e4=Engine(c4); e4.run(); r4=e4.results()
    insMax=float(np.nanmax(r4['errPosIns'])); fusMax=float(np.nanmax(r4['errPosFus']))
    velMax=float(np.nanmax(r4['errVelFus']))
    assert insMax>40, f"INS drift unexpectedly small: {insMax:.1f}"
    assert fusMax<8, f"ZUPT failed to bound position: {fusMax:.2f}"
    assert velMax<0.3, f"ZUPT failed to pin velocity: {velMax:.3f}"
    assert e4.zuptCount>500, f"ZUPT fired too rarely: {e4.zuptCount}"

    # ---------- Baro aiding: climbing, GNSS disabled ----------
    c5=default_config()
    c5['Traj'].update(type='Climb', speed=10.0, climbRate=3.0)
    c5['Sim']['duration']=60.0
    c5['IMU']['accelBiasMg']=[0,0,10]
    c5['GNSS']['enabled']=False
    c5['Align']['enabled']=False
    c5['Baro'].update(enabled=True, sigma=1.0, rate=10.0)
    e5=Engine(c5); e5.run(); r5=e5.results()
    insDown=float(abs(r5['insP'][2,-1]-r5['truthP'][2,-1]))
    fusDown=float(np.nanmax(np.abs(r5['fusP'][2,:]-r5['truthP'][2,:])))
    assert insDown>40, f"vertical INS drift unexpectedly small: {insDown:.1f}"
    assert fusDown<8, f"baro failed to bound vertical error: {fusDown:.2f}"
    print(f"      aiding: GM std={std.mean():.2f}m rho1={rho:.3f}; ZUPT pos {fusMax:.2f}m (INS {insMax:.0f}m, n={e4.zuptCount}); baro down {fusDown:.2f}m (INS {insDown:.0f}m)")

print("="*60)
check('test_utils', t_utils)
check('test_perfect_match', t_perfect)
check('test_ins_drift', t_drift)
check('test_ekf_convergence', t_ekf)
check('test_alignment', t_align)
check('test_variable_dt', t_vdt)
check('test_gnss_dropout', t_dropout)
check('test_time_alignment', t_time_alignment)
check('test_aiding', t_aiding)
print("="*60)
passed=[r for r in results if r[1]]
print(f"Result: {len(passed)}/{len(results)} passed")
if len(passed) != len(results):
    sys.exit(1)
