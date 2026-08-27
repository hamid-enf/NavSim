#!/usr/bin/env python3
"""Generate real simulation data (via the project's own Python mirror) for
the educational video charts.  Saves .npz files into ./data/."""
import os, sys, copy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "tools"))
from navsim_mirror import *  # noqa

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)

def no_imu_errors(cfg):
    for f in ['useGyroBias','useGyroNoise','useGyroSF','useGyroMis',
              'useAccelBias','useAccelNoise','useAccelSF','useAccelMis']:
        cfg['IMU'][f] = False
    return cfg

# ------------------------------------------------------------------ 1. dropout
cfg = default_config()
cfg['Sim']['duration'] = 120
cfg['Traj']['type'] = 'Circle'
cfg['Fusion']['mode'] = 'loose'
cfg['Align']['enabled'] = True; cfg['Align']['duration'] = 5
cfg['Align']['applyUserErr'] = False
cfg['GNSS']['useDropout'] = True; cfg['GNSS']['dropoutText'] = '40 70'
cfg['IMU']['gyroBiasDps'] = [0.1, -0.05, 0.05]
cfg['IMU']['accelBiasMg'] = [5, -3, 2]
e = Engine(cfg); e.run(); d = e.results()
ins_only = copy.deepcopy(cfg); ins_only['Fusion']['mode'] = 'ins'
ei = Engine(ins_only); ei.run(); di = ei.results()
np.savez(os.path.join(OUT, "dropout.npz"),
         t=d['t'], errIns=d['errPosIns'], errFus=d['errPosFus'],
         errInsOnly=di['errPosIns'], sigP=d['sigP'], gnssFlag=d['gnssFlag'])
inout = (d['t'] >= 55) & (d['t'] <= 69); post = d['t'] >= 80
print("dropout: in-outage fused %.2f m (INS-only %.2f m), post %.2f m"
      % (d['errPosFus'][inout].mean(), di['errPosIns'][inout].mean(),
         d['errPosFus'][post].mean()))

# ------------------------------------------------------------------ 2. gyro bias estimation
cfg = default_config()
cfg['Sim']['duration'] = 120
cfg['Traj']['type'] = 'FigureEight'
cfg['Fusion']['mode'] = 'loose'
cfg['Align']['enabled'] = True; cfg['Align']['duration'] = 5
cfg['Align']['applyUserErr'] = True; cfg['Align']['userErrDeg'] = [2, 2, 10]
cfg['IMU']['gyroBiasDps'] = [0.5, -0.3, 0.2]
cfg['IMU']['accelBiasMg'] = [20, -15, 10]
cfg['GNSS']['posSigmaH'] = 2; cfg['GNSS']['posSigmaV'] = 4
e = Engine(cfg); e.run(); d = e.results()
bg = np.degrees(d['calBg'])
ba = d['calBa']
np.savez(os.path.join(OUT, "gyrobias.npz"), t=d['t'], calBg=bg, calBa=ba,
         errPosFus=d['errPosFus'], errAttFus=np.degrees(d['errAttFus']),
         sigA=np.degrees(d['sigA']))
print("gyrobias: bgEst final =", np.round(bg[:, -1], 3), "deg/s")

# ------------------------------------------------------------------ 3. accel bias drift (1/2 b t^2)
cfg = default_config()
cfg['Sim']['duration'] = 120
cfg['Fusion']['mode'] = 'ins'
cfg['Align']['enabled'] = False
no_imu_errors(cfg)
cfg['IMU']['useAccelBias'] = True; cfg['IMU']['accelBiasMg'] = [10, 0, 0]
cfg['Traj']['type'] = 'Straight'; cfg['Traj']['speed'] = 0
e = Engine(cfg); e.run(); d = e.results()
b = 10e-3 * 9.80665
theory = 0.5 * b * d['t']**2
np.savez(os.path.join(OUT, "accelbias.npz"), t=d['t'], errIns=d['errPosIns'], theory=theory)
print("accelbias: actual %.1f m vs theory %.1f m" % (d['errPosIns'][-1], theory[-1]))

# ------------------------------------------------------------------ 4. alignment convergence (1/sqrt(n))
cfg = default_config()
cfg['Traj']['type'] = 'Straight'; cfg['Traj']['speed'] = 0
cfg['Sim']['duration'] = 30
cfg['Align']['enabled'] = True; cfg['Align']['duration'] = 25
cfg['Align']['coarseLevel'] = True; cfg['Align']['applyUserErr'] = False
cfg['Align']['magHeadingSigmaDeg'] = 0.5
cfg['IMU']['useGyroBias'] = False; cfg['IMU']['useAccelBias'] = False
e = Engine(cfg)
while e.t < cfg['Align']['duration']:
    e.step()
r = e.results()
am = ~np.isnan(r['alignEst'][0]); idx = np.where(am)[0]
err = np.degrees(np.linalg.norm(wrapPi(r['alignEst'][0:2, idx] - r['truthE'][0:2, idx]), axis=0))
np.savez(os.path.join(OUT, "align.npz"), n=np.arange(1, len(err)+1), err=err)
print("align: %.3f deg -> %.3f deg" % (err[int(0.1*len(err))], err[-1]))

# ------------------------------------------------------------------ 5. sigma growth during dropout (for prediction panel)
d = np.load(os.path.join(OUT, "dropout.npz"))
np.savez(os.path.join(OUT, "sigma.npz"), t=d['t'], sigP=d['sigP'])
print("sigma: pos sigma range %.2f - %.2f m"
      % (np.nanmin(d['sigP'][0]), np.nanmax(d['sigP'][0])))

print("DATA DONE")
