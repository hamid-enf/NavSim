#!/usr/bin/env python3
"""Faithful Python mirror of the NavSim MATLAB core (for offline validation of
the algorithms: truth -> IMU -> INS -> GNSS -> EKF). Line-by-line analog of the
.m implementation; used to verify math, signs and test expectations."""
import numpy as np

D2R = np.pi/180.0
R2D = 180.0/np.pi

def skew(v):
    x,y,z = v
    return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])

def wrapPi(a):
    return (a + np.pi)%(2*np.pi) - np.pi

def eul2dcm(e):
    r,p,y = e; cr,sr,cp,sp,cy,sy = np.cos(r),np.sin(r),np.cos(p),np.sin(p),np.cos(y),np.sin(y)
    return np.array([[cp*cy, sr*sp*cy-cr*sy, cr*sp*cy+sr*sy],
                     [cp*sy, sr*sp*sy+cr*cy, cr*sp*sy-sr*cy],
                     [-sp,    sr*cp,          cr*cp]])

def dcm2eul(C):
    return np.array([np.arctan2(C[2,1],C[2,2]),
                     -np.arcsin(np.clip(C[2,0],-1,1)),
                     np.arctan2(C[1,0],C[0,0])])

def quatMul(q1,q2):
    w1,x1,y1,z1 = q1; w2,x2,y2,z2 = q2
    return np.array([w1*w2-x1*x2-y1*y2-z1*z2,
                     w1*x2+x1*w2+y1*z2-z1*y2,
                     w1*y2-x1*z2+y1*w2+z1*x2,
                     w1*z2+x1*y2-y1*x2+z1*w2])

def quat2dcm(q):
    q = q/np.linalg.norm(q); w,x,y,z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w)],
                     [2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y)]])

def dcm2quat(C):
    tr = C[0,0]+C[1,1]+C[2,2]
    if tr>0:
        s=np.sqrt(tr+1.0)*2; q=np.array([0.25*s,(C[2,1]-C[1,2])/s,(C[0,2]-C[2,0])/s,(C[1,0]-C[0,1])/s])
    elif C[0,0]>C[1,1] and C[0,0]>C[2,2]:
        s=np.sqrt(1.0+C[0,0]-C[1,1]-C[2,2])*2; q=np.array([(C[2,1]-C[1,2])/s,0.25*s,(C[0,1]+C[1,0])/s,(C[0,2]+C[2,0])/s])
    elif C[1,1]>C[2,2]:
        s=np.sqrt(1.0+C[1,1]-C[0,0]-C[2,2])*2; q=np.array([(C[0,2]-C[2,0])/s,(C[0,1]+C[1,0])/s,0.25*s,(C[1,2]+C[2,1])/s])
    else:
        s=np.sqrt(1.0+C[2,2]-C[0,0]-C[1,1])*2; q=np.array([(C[1,0]-C[0,1])/s,(C[0,2]+C[2,0])/s,(C[1,2]+C[2,1])/s,0.25*s])
    if q[0]<0: q=-q
    return q/np.linalg.norm(q)

def eul2quat(e): return dcm2quat(eul2dcm(e))
def quat2eul(q): return dcm2eul(quat2dcm(q))

def eulRates2body(eul, eulDot):
    r,th = eul[0],eul[1]; rd,thd,yd = eulDot
    return np.array([rd - yd*np.sin(th),
                     thd*np.cos(r) + yd*np.sin(r)*np.cos(th),
                    -thd*np.sin(r) + yd*np.cos(r)*np.cos(th)])

def deltaQuat(a):
    a=np.asarray(a,float); n=np.linalg.norm(a)
    if n<1e-12: return np.concatenate([[1.0], a/2])
    return np.concatenate([[np.cos(n/2)], a/n*np.sin(n/2)])

G0 = 9.80665

# ---------------------------------------------------------------- trajectory
def make_traj(tp, P):
    g = 9.80665; h0 = np.radians(P.get('heading0',0)); V=P['speed']; R=max(P['radius'],1); alt=P['alt0']
    if tp=='Straight':
        pv = lambda t: (np.array([V*t*np.cos(h0),V*t*np.sin(h0),-alt]),
                        np.array([V*np.cos(h0),V*np.sin(h0),0.0]), np.zeros(3))
    elif tp=='Circle':
        w=V/R
        pv = lambda t: (np.array([R*np.sin(w*t),R*(1-np.cos(w*t)),-alt]),
                        np.array([V*np.cos(w*t),V*np.sin(w*t),0.0]),
                        np.array([-V*w*np.sin(w*t),V*w*np.cos(w*t),0.0]))
    elif tp=='FigureEight':
        w=V/R
        pv = lambda t: (np.array([R*np.sin(w*t),(R/2)*np.sin(2*w*t),-alt]),
                        np.array([V*np.cos(w*t),V*np.cos(2*w*t),0.0]),
                        np.array([-V*w*np.sin(w*t),-2*V*w*np.sin(2*w*t),0.0]))
    elif tp=='Acceleration':
        a0=P['accel']
        pv = lambda t: (np.array([(V*t+0.5*a0*t*t)*np.cos(h0),(V*t+0.5*a0*t*t)*np.sin(h0),-alt]),
                        np.array([(V+a0*t)*np.cos(h0),(V+a0*t)*np.sin(h0),0.0]),
                        np.array([a0*np.cos(h0),a0*np.sin(h0),0.0]))
    elif tp=='Climb':
        rc=P['climbRate']
        pv = lambda t: (np.array([V*t*np.cos(h0),V*t*np.sin(h0),-(alt+rc*t)]),
                        np.array([V*np.cos(h0),V*np.sin(h0),-rc]), np.zeros(3))
    elif tp=='Descent':
        rc=P['climbRate']
        # No artificial ground clamp: it would create an unmodelled
        # instantaneous velocity jump and break perfect-IMU consistency.
        pv = lambda t: (np.array([V*t*np.cos(h0),V*t*np.sin(h0),-alt+rc*t]),
                        np.array([V*np.cos(h0),V*np.sin(h0),rc]), np.zeros(3))
    elif tp=='Turn':
        dur=P.get('durationVal',120); T1=0.3*dur; Tr=min(5,max(2,0.2*dur))
        w=np.radians(P['turnRate']); w = w if abs(w)>1e-9 else 1e-9
        R0=np.array([[np.cos(h0),-np.sin(h0)],[np.sin(h0),np.cos(h0)]])
        def f(t):
            if t<=T1:
                return (np.array([V*t*np.cos(h0),V*t*np.sin(h0),-alt]),
                        np.array([V*np.cos(h0),V*np.sin(h0),0.0]), np.zeros(3))
            tau=t-T1; u=np.clip(tau/Tr,0,1)
            ss=10*u**3-15*u**4+6*u**5
            if tau<Tr:
                sd=(30*u**2-60*u**3+30*u**4)/Tr
                sdd=(60*u-180*u**2+120*u**3)/(Tr**2)
            else:
                sd=0.0; sdd=0.0
            x=V/w*np.sin(w*tau); y0=V/w*(1-np.cos(w*tau))
            vx=V*np.cos(w*tau); vy0=V*np.sin(w*tau)
            ax=-V*w*np.sin(w*tau); ay0=V*w*np.cos(w*tau)
            xy=np.array([x,y0*ss]); vv=np.array([vx,vy0*ss+y0*sd])
            aa=np.array([ax,ay0*ss+2*vy0*sd+y0*sdd])
            p1=np.array([V*T1*np.cos(h0),V*T1*np.sin(h0)])
            pn=p1+R0@xy; vn=R0@vv; an=R0@aa
            return (np.array([pn[0],pn[1],-alt]),np.array([vn[0],vn[1],0.0]),
                    np.array([an[0],an[1],0.0]))
        pv=f
    elif tp=='Combined3D':
        w=V/R; rc=P['climbRate']
        pv = lambda t: (np.array([R*np.sin(w*t),R*(1-np.cos(w*t)),-(alt+30*np.sin(w*t)+rc*t)]),
                        np.array([V*np.cos(w*t),V*np.sin(w*t),-(30*w*np.cos(w*t)+rc)]),
                        np.array([-V*w*np.sin(w*t),V*w*np.cos(w*t),30*w*w*np.sin(w*t)]))
    else:
        raise ValueError(tp)

    # Curved trajectories are authored in a convenient local orientation,
    # then rotated so heading0 is their actual initial horizontal heading.
    if tp in ('Circle', 'FigureEight', 'Combined3D'):
        pv0 = pv
        _, v0, _ = pv0(0.0)
        base = np.arctan2(v0[1], v0[0]) if np.hypot(v0[0], v0[1]) > 1e-12 else 0.0
        ang = h0 - base
        Rh = np.array([[np.cos(ang), -np.sin(ang)],
                       [np.sin(ang),  np.cos(ang)]])
        def pv(t):
            p, v, a = pv0(t)
            p = p.copy(); v = v.copy(); a = a.copy()
            p[:2] = Rh @ p[:2]; v[:2] = Rh @ v[:2]; a[:2] = Rh @ a[:2]
            return p, v, a

    def attOf(t):
        _,v,a = pv(t)
        Vh = np.hypot(v[0],v[1])
        if Vh>1e-6:
            yaw=np.arctan2(v[1],v[0]); pitch=np.arctan2(-v[2],Vh)
            yd=(v[0]*a[1]-v[1]*a[0])/max(Vh*Vh,1e-3)
            roll=np.clip(np.arctan(Vh*yd/g),-1.0,1.0)
        else:
            yaw=h0; pitch=np.arctan2(-v[2],0.5); roll=0.0
        return np.array([roll,pitch,yaw])

    def truth(t):
        p,v,a = pv(t)
        e = attOf(t)
        hh=1e-3
        ep=attOf(t+hh); em=attOf(max(t-hh,0.0))
        if t<hh: ed=wrapPi(ep-e)/hh
        else:    ed=wrapPi(ep-em)/(2*hh)
        return dict(t=t,p=p,v=v,a=a,eul=e,eulDot=ed)
    return truth

# ---------------------------------------------------------------- models
class IMU:
    def __init__(s,c):
        s.c=c
        I=c['IMU']
        s.bgBase = np.radians(np.array(I['gyroBiasDps'])) if I['useGyroBias'] else np.zeros(3)
        s.baBase = np.array(I['accelBiasMg'])*1e-3*9.80665 if I['useAccelBias'] else np.zeros(3)
        Sg = np.diag(1+np.array(I['gyroSFPpm'])*1e-6) if I['useGyroSF'] else np.eye(3)
        Sa = np.diag(1+np.array(I['accelSFPpm'])*1e-6) if I['useAccelSF'] else np.eye(3)
        Gm = np.eye(3)+skew(np.radians(np.array(I['gyroMisDeg']))) if I['useGyroMis'] else np.eye(3)
        Am = np.eye(3)+skew(np.radians(np.array(I['accelMisDeg']))) if I['useAccelMis'] else np.eye(3)
        s.Mg = Gm@Sg; s.Ma = Am@Sa
        s.bgRW=np.zeros(3); s.baRW=np.zeros(3); s.rng=np.random.default_rng(s.c['Sim']['seed'])
    def measure(s,wT,fT,dt):
        I=s.c['IMU']
        if I['useGyroBias'] and I['gyroBiasRW']>0:
            s.bgRW += np.radians(I['gyroBiasRW'])*np.sqrt(dt)*s.rng.standard_normal(3)
        if I['useAccelBias'] and I['accelBiasRW']>0:
            s.baRW += I['accelBiasRW']*np.sqrt(dt)*s.rng.standard_normal(3)
        bg=s.bgBase+s.bgRW; ba=s.baBase+s.baRW
        ng = np.radians(I['gyroARWDpsHz'])/np.sqrt(dt)*s.rng.standard_normal(3) if I['useGyroNoise'] else np.zeros(3)
        na = I['accelVRW']/np.sqrt(dt)*s.rng.standard_normal(3) if I['useAccelNoise'] else np.zeros(3)
        return s.Mg@wT+bg+ng, s.Ma@fT+ba+na, dict(bg=bg,ba=ba)

class GNSS:
    def __init__(s,c):
        s.c=c; s.nextEpoch=0.0; s.queue=[]; s.last=None
        s.gmState=np.zeros(3); s.gmInit=False; s.lastGmT=0.0
        G=c['GNSS']
        s.windows=[]
        for seg in str(G['dropoutText']).split(';'):
            vals=[float(x) for x in seg.split()]
            if len(vals)>=2: s.windows.append((vals[0],vals[1]))
        s.rng=np.random.default_rng(c['Sim']['seed']+7)
    def inDropout(s,t):
        G=s.c['GNSS']
        if not G['useDropout']: return False
        for a,b in s.windows:
            if a<=t<=b: return True
        if G['randDropProb']>0 and s.rng.random()<G['randDropProb']: return True
        return False
    def advanceGm(s,t):
        # Stationary Gauss-Markov correlated error with exact transition.
        G=s.c['GNSS']
        if not s.gmInit:
            s.gmState=G['gmSigma']*s.rng.standard_normal(3); s.gmInit=True
        else:
            dt=max(t-s.lastGmT,0.0); phi=np.exp(-dt/G['gmTau'])
            sig=G['gmSigma']*np.sqrt(max(1.0-phi*phi,0.0))
            s.gmState=phi*s.gmState+sig*s.rng.standard_normal(3)
        s.lastGmT=t
        return s.gmState.copy()
    def update(s,t,truth):
        G=s.c['GNSS']
        hasG=False; z=None; evt=''
        if not G['enabled']: return False,None,''
        if t >= s.nextEpoch - 1e-12:
            rate=max(G['rate'],1e-3); s.nextEpoch += 1.0/rate
            if s.inDropout(t):
                evt='DROPOUT'
            else:
                sH=G['posSigmaH']*(1 if G['useNoise'] else 0)
                sV=G['posSigmaV']*(1 if G['useNoise'] else 0)
                p=truth['p']+np.array(G['biasNed'])+np.array([sH*s.rng.standard_normal(),sH*s.rng.standard_normal(),sV*s.rng.standard_normal()])
                if G.get('useGmNoise',False):
                    p = p + s.advanceGm(t)
                isOut=False
                if G['useOutlier'] and s.rng.random()<G['outlierProb']:
                    p = p + G['outlierMag']*(2*s.rng.random(3)-1); isOut=True
                z=dict(p=p, R=np.diag([max(sH,0.05)**2,max(sH,0.05)**2,max(sV,0.05)**2]),
                       outlier=isOut, tEmit=t+G['delay'], hasVel=G['enableVel'], v=None, Rv=None)
                if G['enableVel']:
                    sVl=G['velSigma']*(1 if G['useNoise'] else 0)
                    z['v']=truth['v']+sVl*s.rng.standard_normal(3)
                    if isOut and G.get('outlierVelSigma',0)>0:
                        z['v']=z['v']+G['outlierVelSigma']*(2*s.rng.random(3)-1)
                    z['Rv']=np.eye(3)*max(sVl,0.01)**2
                s.queue.append(z); evt='MEAS_OUTLIER' if isOut else 'MEAS'
        if s.queue and s.queue[0]['tEmit'] <= t+1e-12:
            z=s.queue.pop(0); hasG=True; s.last=z
        return hasG,z,evt

class Baro:
    def __init__(s,c):
        s.c=c; s.nextEpoch=0.0; s.gmState=0.0; s.gmInit=False; s.lastGmT=0.0
        s.rng=np.random.default_rng(c['Sim']['seed']+13)
    def advanceGm(s,t):
        B=s.c['Baro']
        if not s.gmInit:
            s.gmState=B['gmSigma']*s.rng.standard_normal(); s.gmInit=True
        else:
            dt=max(t-s.lastGmT,0.0); phi=np.exp(-dt/B['gmTau'])
            sig=B['gmSigma']*np.sqrt(max(1.0-phi*phi,0.0))
            s.gmState=phi*s.gmState+sig*s.rng.standard_normal()
        s.lastGmT=t
        return s.gmState
    def update(s,t,hTrue):
        if not s.c['Baro']['enabled']: return False,None
        if t >= s.nextEpoch - 1e-12:
            rate=max(s.c['Baro']['rate'],1e-3)
            s.nextEpoch += 1.0/rate
            if s.nextEpoch < t: s.nextEpoch = t + 1.0/rate
            B=s.c['Baro']
            drift = s.advanceGm(t) if B['gmSigma']>0 else 0.0
            sig=B['sigma']
            z=dict(h=hTrue+B['bias']+drift+sig*s.rng.standard_normal(),
                   R=max(sig,0.05)**2, tMeas=t)
            return True,z
        return False,None

class INS:
    def __init__(s):
        s.p=np.zeros(3); s.v=np.zeros(3); s.q=np.array([1.,0,0,0]); s.C=np.eye(3)
        s.grav=9.80665; s.fn=np.zeros(3)
    def reset(s,p0,v0,eul0,grav=9.80665):
        s.p=np.array(p0,float); s.v=np.array(v0,float)
        s.q=eul2quat(eul0); s.C=quat2dcm(s.q); s.grav=grav
    def step(s,w,f,dt,grav=None):
        if grav is not None: s.grav=grav
        qN=quatMul(s.q,deltaQuat(w*dt)); qN=qN/np.linalg.norm(qN)
        Cn=quat2dcm(qN); Cm=0.5*(s.C+Cn)
        fn=Cm@f
        vv=s.v+(fn+np.array([0,0,s.grav]))*dt
        s.p=s.p+0.5*(s.v+vv)*dt
        s.v=vv; s.q=qN; s.C=Cn; s.fn=fn
    def correct(s,dp,dv,dphi):
        s.p=s.p+dp; s.v=s.v+dv
        corrected=(np.eye(3)-skew(dphi))@s.C
        s.q=dcm2quat(corrected)
        s.C=quat2dcm(s.q)
    def eul(s): return dcm2eul(s.C)

class Align:
    def __init__(s,c,truth0,rng):
        A=c['Align']; s.c=c
        s.n=0; s.sumF=np.zeros(3); s.t0=0.0
        s.truthEul0=truth0['eul']; s.yawMagErr=np.radians(A['magHeadingSigmaDeg'])*rng.standard_normal()
        s.coarseErr=np.radians(A.get('coarseMovingSigmaDeg',3.0))*rng.standard_normal(3)
        s.isStatic=(float(np.linalg.norm(truth0['v']))<=1.0 and
                    float(np.linalg.norm(truth0['a']))<=0.1 and
                    float(np.linalg.norm(truth0['eulDot']))<=np.radians(0.1))
        s.estEul=truth0['eul']+np.array([0.5,0.5,1.0])
        s.active=A['enabled'] and A['duration']>0
    def update(s,fm,truth):
        if not s.active: return
        s.n+=1
        if s.isStatic:
            s.sumF+=fm; mf=s.sumF/s.n
            if s.c['Align']['coarseLevel']:
                phi=np.arctan2(-mf[1],-mf[2]); th=np.arctan2(mf[0],np.hypot(mf[1],mf[2]))
                s.estEul=np.array([phi,th,s.truthEul0[2]+s.yawMagErr])
            else:
                s.estEul=s.truthEul0+np.array([0,0,s.yawMagErr])
        else:
            s.estEul=truth['eul']+s.coarseErr
    def finalize(s):
        e = s.estEul if s.active else s.truthEul0
        e = e.copy()
        if s.c['Align']['applyUserErr']:
            e = e + np.radians(np.array(s.c['Align']['userErrDeg']))
        return e

class EKF:
    def initState(s,c):
        F=c['Fusion']
        sig=np.array([F['p0pos']]*3+[F['p0vel']]*3+[np.radians(F['p0attDeg'])]*3+
                     [np.radians(F['p0gyroBiasDps'])]*3+[F['p0accelBias']]*3)
        s.P=np.diag(sig**2); s.x=np.zeros(15); s.ok=True
        s.qa=F['qa']; s.qg=F['qg']; s.qbg=F['qbg']; s.qba=F['qba']; s.qScale=F['qScale']; s.rScale=F['rScale']
        s.lastInnov=np.zeros(3); s.lastNIS=0.0
    def predict(s,C,fb,dt):
        fn=C@fb
        Fm=np.eye(15)
        Fm[0:3,3:6]=np.eye(3)*dt
        Fm[3:6,6:9]=skew(fn)*dt
        Fm[3:6,12:15]=-C*dt
        Fm[6:9,9:12]=C*dt   # error = true - est convention
        qa=(s.qa*s.qScale)**2; qg=(np.radians(s.qg)*s.qScale)**2
        qbg=(np.radians(s.qbg)*s.qScale)**2; qba=(s.qba*s.qScale)**2
        Qd=np.zeros((15,15))
        Qd[0:3,0:3]=np.eye(3)*qa*dt**3/3
        Qd[0:3,3:6]=np.eye(3)*qa*dt**2/2
        Qd[3:6,0:3]=Qd[0:3,3:6].T
        Qd[3:6,3:6]=np.eye(3)*qa*dt
        Qd[6:9,6:9]=np.eye(3)*qg*dt
        Qd[9:12,9:12]=np.eye(3)*qbg*dt
        Qd[12:15,12:15]=np.eye(3)*qba*dt
        s.P=Fm@s.P@Fm.T+Qd; s.P=0.5*(s.P+s.P.T)
    def _kalm(s,z,H,R):
        innov=z-H@s.x
        S=H@s.P@H.T+R
        K=s.P@H.T@np.linalg.inv(S)
        s.x=s.x+K@innov
        IKH=np.eye(15)-K@H
        s.P=IKH@s.P@IKH.T+K@R@K.T; s.P=0.5*(s.P+s.P.T)
        s.lastInnov=innov; s.lastNIS=float(innov.T@np.linalg.solve(S,innov))
    def updatePos(s,zp,R): s._kalm(zp,np.hstack([np.eye(3),np.zeros((3,12))]),R*s.rScale)
    def updateVel(s,zv,Rv): s._kalm(zv,np.hstack([np.zeros((3,3)),np.eye(3),np.zeros((3,9))]),Rv*s.rScale)
    def updateBaro(s,hMeas,hIns,R):
        # delta_h = -delta_p_D -> H = [0 0 -1 0 ... 0]
        H=np.zeros((1,15)); H[0,2]=-1.0
        s._kalm(np.array([hMeas-hIns]),H,np.array([[R*s.rScale]]))
    def consume(s):
        dx=s.x.copy(); s.x[:]=0; return dx
    def sigmas(s): return np.sqrt(np.maximum(np.diag(s.P),0))

# ---------------------------------------------------------------- default config (mirror of defaultConfig.m)
def default_config():
    return dict(
      Sim=dict(dt=0.01,duration=120.0,speed=1,mode='realtime',seed=1,variableDt='off',dtJitter=0.5,chunkFast=400),
      Traj=dict(type='Circle',speed=15,radius=200,alt0=100,climbRate=3,turnRate=3,heading0=0,accel=1.5,
                userExpr='[10*t; 100*sin(0.05*t); -100]'),
      IMU=dict(useGyroBias=True,useGyroNoise=True,useGyroSF=False,useGyroMis=False,
               useAccelBias=True,useAccelNoise=True,useAccelSF=False,useAccelMis=False,
               gyroBiasDps=[0.02,-0.015,0.01],gyroARWDpsHz=0.01,gyroSFPpm=[50,-30,20],
               gyroMisDeg=[0.02,0.01,-0.015],gyroBiasRW=0.0,
               accelBiasMg=[2,-1.5,1],accelVRW=0.02,accelSFPpm=[80,40,-60],
               accelMisDeg=[0.02,-0.02,0.01],accelBiasRW=0.0),
      GNSS=dict(enabled=True,rate=1.0,useNoise=True,posSigmaH=1.5,posSigmaV=3.0,enableVel=False,
                velSigma=0.05,biasNed=[0,0,0],useDropout=False,dropoutText='60 75',randDropProb=0.0,
                useOutlier=False,outlierProb=0.02,outlierMag=50,delay=0.0,
                useGmNoise=False,gmSigma=2.0,gmTau=30.0,outlierVelSigma=0.0),
      Baro=dict(enabled=False,rate=10.0,sigma=1.0,bias=0.0,gmSigma=0.0,gmTau=60.0),
      INS=dict(gravity=9.80665,initPosErr=[0,0,0],initVelErr=[0,0,0],refLat=50.478,refLon=12.365,refH=430),
      Align=dict(enabled=True,duration=10.0,coarseLevel=True,magHeadingSigmaDeg=1.0,
                 coarseMovingSigmaDeg=3.0,applyUserErr=False,userErrDeg=[0,0,5]),
      Fusion=dict(mode='loose',useVel=False,qa=0.05,qg=0.02,qbg=0.002,qba=0.005,
                  p0pos=5.0,p0vel=0.5,p0attDeg=5.0,p0gyroBiasDps=0.5,p0accelBias=0.3,
                  qScale=1.0,rScale=1.0,nisGateBaro=10.83,
                  useZupt=False,zuptAccelG=0.05,zuptRateDps=3.0,zuptHoldS=1.0,zuptSigma=0.05))

class Engine:
    def __init__(s,cfg):
        s.configure(cfg)
    def configure(s,cfg):
        s.c=cfg
        P=dict(cfg['Traj']); P['durationVal']=cfg['Sim']['duration']
        s.traj=make_traj(P['type'],P)
        s.imu=IMU(cfg); s.gnss=GNSS(cfg); s.baro=Baro(cfg); s.ins=INS(); s.insPure=INS(); s.ekf=EKF()
        s.zuptRun=0.0; s.zuptCount=0
        s.rs=np.random.default_rng(cfg['Sim']['seed'])
        s.t=0.0; s.k=0; s.istep=0; s.done=False
        s.calBg=np.zeros(3); s.calBa=np.zeros(3)
        s.lastGnssP=np.full(3,np.nan); s.lastGnssV=np.full(3,np.nan); s.gnssEvent=''
        s.align=Align(cfg,s.traj(0.0),s.rs)
        s.ekf.ok=False
        if s.align.active: s.phase='align'
        else:
            s.phase='nav'; s.initNav(s.traj(0.0))
        s.log=[]
    def initNav(s,truthNow):
        eul0=s.align.finalize()
        p0=truthNow['p']+np.array(s.c['INS']['initPosErr'],float)
        v0=truthNow['v']+np.array(s.c['INS']['initVelErr'],float)
        s.ins.reset(p0,v0,eul0,s.c['INS']['gravity'])
        s.insPure.reset(p0,v0,eul0,s.c['INS']['gravity'])
        if s.c['Fusion']['mode']=='loose': s.ekf.initState(s.c)
    def pickDt(s):
        c=s.c['Sim']
        if c['variableDt']=='jitter':
            return c['dt']*max(0.2,1+c['dtJitter']*(2*s.rs.random()-1))
        if c['variableDt']=='tworate':
            return c['dt'] if (s.istep%20)<10 else c['dt']*4
        return c['dt']
    def fusionOn(s): return s.c['Fusion']['mode']=='loose'
    def step(s):
        if s.done: return
        c=s.c
        remaining=c['Sim']['duration']-s.t
        if remaining <= 1e-10*max(1.0,c['Sim']['duration']):
            s.t=c['Sim']['duration']; s.done=True; s.phase='done'; return
        dt=min(s.pickDt(),remaining); s.istep+=1
        truth=s.traj(s.t)
        g=c['INS']['gravity']-3.086e-6*(-truth['p'][2]); gn=np.array([0,0,g])
        Ct=eul2dcm(truth['eul'])
        wT=eulRates2body(truth['eul'],truth['eulDot'])
        fT=Ct.T@(truth['a']-gn)
        wm,fm,dbg=s.imu.measure(wT,fT,dt)
        hasG,z,evt=s.gnss.update(s.t,truth)
        if evt: s.gnssEvent=evt
        if hasG:
            s.lastGnssP=z['p']
            if z['hasVel']: s.lastGnssV=z['v']
        hasB,zb=s.baro.update(s.t, s.c['INS']['refH']-truth['p'][2])

        if (s.phase=='align' and
                (s.t-s.align.t0)>=c['Align']['duration']-1e-10*max(1.0,c['Align']['duration'])):
            s.align.update(fm,truth)
            s.phase='nav'; s.initNav(truth)

        row=dict(t=s.t,dt=dt,truthP=truth['p'].copy(),truthV=truth['v'].copy(),truthE=truth['eul'].copy(),
                 gyroT=wT,accT=fT,gyroM=wm,accM=fm,imuBg=dbg['bg'],imuBa=dbg['ba'],
                 insP=(s.insPure.p.copy() if s.phase=='nav' else np.full(3,np.nan)),
                 insV=(s.insPure.v.copy() if s.phase=='nav' else np.full(3,np.nan)),
                 insE=(s.insPure.eul().copy() if s.phase=='nav' else np.full(3,np.nan)),
                 fusP=(s.ins.p.copy() if s.phase=='nav' else np.full(3,np.nan)),
                 fusV=(s.ins.v.copy() if s.phase=='nav' else np.full(3,np.nan)),
                 fusE=(s.ins.eul().copy() if s.phase=='nav' else np.full(3,np.nan)),
                 calBg=s.calBg.copy(),calBa=s.calBa.copy(),
                 gnssP=np.full(3,np.nan),gnssFlag=np.nan,alignEst=np.full(3,np.nan),
                 sigP=np.full(3,np.nan),sigA=np.full(3,np.nan))
        if hasG:
            row['gnssP']=z['p']; row['gnssFlag']=1+(1 if z['outlier'] else 0)
        if s.phase=='align':
            s.align.update(fm,truth)
            row['alignEst']=s.align.estEul.copy()
        else:
            if hasG and s.fusionOn():
                if not s.ekf.ok: s.ekf.initState(c)
                s.ekf.updatePos(z['p']-s.ins.p,z['R'])
                if z['hasVel'] and c['Fusion']['useVel']:
                    s.ekf.updateVel(z['v']-s.ins.v,z['Rv'])
                dx=s.ekf.consume()
                s.ins.correct(dx[0:3],dx[3:6],dx[6:9])
                s.calBg=s.calBg+dx[9:12]; s.calBa=s.calBa+dx[12:15]
            if s.fusionOn():
                if c['Fusion']['useZupt']:
                    F=c['Fusion']
                    stationary=(abs(np.linalg.norm(fm)-s.ins.grav)<=F['zuptAccelG']*9.80665 and
                                np.linalg.norm(wm)<=np.radians(F['zuptRateDps']))
                    s.zuptRun = s.zuptRun+dt if stationary else 0.0
                    if stationary and s.zuptRun>=F['zuptHoldS']:
                        s.ekf.updateVel(np.zeros(3)-s.ins.v, np.eye(3)*F['zuptSigma']**2)
                        dx=s.ekf.consume()
                        s.ins.correct(dx[0:3],dx[3:6],dx[6:9])
                        s.calBg=s.calBg+dx[9:12]; s.calBa=s.calBa+dx[12:15]
                        s.zuptCount+=1
                if hasB:
                    s.ekf.updateBaro(zb['h'], s.c['INS']['refH']-s.ins.p[2], zb['R'])
                    dx=s.ekf.consume()
                    s.ins.correct(dx[0:3],dx[3:6],dx[6:9])
                    s.calBg=s.calBg+dx[9:12]; s.calBa=s.calBa+dx[12:15]
            row['insP']=s.insPure.p.copy(); row['insV']=s.insPure.v.copy(); row['insE']=s.insPure.eul().copy()
            row['fusP']=s.ins.p.copy(); row['fusV']=s.ins.v.copy(); row['fusE']=s.ins.eul().copy()
            row['calBg']=s.calBg.copy(); row['calBa']=s.calBa.copy()
            if s.ekf.ok:
                sg=s.ekf.sigmas(); row['sigP']=sg[0:3]; row['sigA']=sg[6:9]
        s.log.append(row); s.k+=1

        if s.phase=='nav':
            wc=wm-s.calBg; fc=fm-s.calBa
            gIns=c['INS']['gravity']-3.086e-6*(-s.ins.p[2])
            gPure=c['INS']['gravity']-3.086e-6*(-s.insPure.p[2])
            s.ins.step(wc,fc,dt,gIns)
            s.insPure.step(wm,fm,dt,gPure)
            if s.fusionOn(): s.ekf.predict(s.ins.C,fc,dt)
        s.t+=dt
        if s.t>=c['Sim']['duration']-1e-10*max(1.0,c['Sim']['duration']):
            s.t=c['Sim']['duration']; s.done=True; s.phase='done'
    def run(s):
        while not s.done: s.step()
    def results(s):
        def col(key): return np.array([r[key] for r in s.log]).T
        d=dict(n=s.k,t=np.array([r['t'] for r in s.log]),dt=np.array([r['dt'] for r in s.log]))
        for key in ['truthP','truthV','truthE','insP','insV','insE','fusP','fusV','fusE',
                    'gnssP','alignEst','sigP','sigA','calBg','calBa','gyroM','accM','gyroT','accT']:
            d[key]=col(key)
        d['gnssFlag']=np.array([r['gnssFlag'] for r in s.log])
        d['errPosIns']=np.linalg.norm(d['insP']-d['truthP'],axis=0)
        d['errPosFus']=np.linalg.norm(d['fusP']-d['truthP'],axis=0)
        d['errVelFus']=np.linalg.norm(d['fusV']-d['truthV'],axis=0)
        d['errAttIns']=np.linalg.norm(wrapPi(d['insE']-d['truthE']),axis=0)
        d['errAttFus']=np.linalg.norm(wrapPi(d['fusE']-d['truthE']),axis=0)
        return d
