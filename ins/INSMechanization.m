classdef INSMechanization < handle
%INSMECHANIZATION Strapdown INS in flat or WGS84 local-level NED mode.
% WGS84 mode includes Earth/transport frame rotation, Coriolis acceleration
% and ECEF position integration.  Optional streaming coning/sculling
% compensation operates on consecutive gyro/accelerometer increments.

properties
    p = zeros(3,1)
    v = zeros(3,1)
    q = [1;0;0;0]
    C = eye(3)
    lla = zeros(3,1)
    rEcef = zeros(3,1)
    refLla = zeros(3,1)
    grav = 9.80665
    fnLast = zeros(3,1)
    prevDtheta = zeros(3,1)
    prevDv = zeros(3,1)
end

methods
    function reset(obj,p0,v0,eul0,cfg)
        obj.p=p0(:); obj.v=v0(:);
        obj.q=eul2quat(eul0); obj.C=quat2dcm(obj.q);
        obj.prevDtheta=zeros(3,1); obj.prevDv=zeros(3,1); obj.fnLast=zeros(3,1);
        if nargin>=5
            obj.grav=cfg.INS.gravity;
            obj.refLla=[cfg.INS.refLat;cfg.INS.refLon;cfg.INS.refH];
        end
        obj.lla=ned2lla(obj.p,obj.refLla);
        obj.rEcef=lla2ecef(obj.lla);
    end

    function step(obj,w,f,dt,cfgOrGravity)
        if nargin<5, cfgOrGravity=obj.grav; end
        if isstruct(cfgOrGravity)
            cfg=cfgOrGravity; useEarth=strcmp(cfg.INS.earthModel,'wgs84');
            useCS=cfg.INS.useConingSculling;
        else
            cfg=[]; useEarth=false; useCS=false; obj.grav=cfgOrGravity;
        end
        dtheta=w(:)*dt; dv=f(:)*dt;
        if useCS
            thetaEff=dtheta+cross(obj.prevDtheta,dtheta)/12;
            dvEff=dv+0.5*cross(dtheta,dv)+ ...
                (cross(obj.prevDtheta,dv)+cross(obj.prevDv,dtheta))/12;
        else
            thetaEff=dtheta; dvEff=dv;
        end
        Cold=obj.C; vOld=obj.v;
        if useEarth
            [wie,wen,win]=earthRatesNED(obj.lla,obj.v,cfg);
            qNew=quatMul(deltaQuat(-win*dt),quatMul(obj.q,deltaQuat(thetaEff)));
            qNew=qNew/norm(qNew); Cnew=quat2dcm(qNew);
            if useCS
                CnavHalf=quat2dcm(deltaQuat(-0.5*win*dt));
                dvSpecific=CnavHalf*Cold*dvEff;
            else
                dvSpecific=0.5*(Cold+Cnew)*f(:)*dt;
            end
            hRel=obj.lla(3)-obj.refLla(3);
            g=localGravity(cfg,hRel,obj.lla(1)); obj.grav=g;
            if cfg.INS.useCoriolis
                coriolis=cross(2*wie+wen,obj.v);
            else
                coriolis=zeros(3,1);
            end
            vv=obj.v+dvSpecific+([0;0;g]-coriolis)*dt;
            Cen=nedRotation(obj.lla);
            rPred=obj.rEcef+Cen'*vv*dt;
            llaPred=ecef2lla(rPred); CenPred=nedRotation(llaPred);
            obj.rEcef=obj.rEcef+0.5*(Cen'*vOld+CenPred'*vv)*dt;
            obj.lla=ecef2lla(obj.rEcef);
            obj.p=lla2ned(obj.lla,obj.refLla);
            obj.fnLast=dvSpecific/dt;
        else
            qNew=quatMul(obj.q,deltaQuat(thetaEff));
            qNew=qNew/norm(qNew); Cnew=quat2dcm(qNew);
            if useCS
                dvSpecific=Cold*dvEff;
            else
                dvSpecific=0.5*(Cold+Cnew)*f(:)*dt;
            end
            vv=obj.v+dvSpecific+[0;0;obj.grav]*dt;
            obj.p=obj.p+0.5*(obj.v+vv)*dt;
            obj.lla=ned2lla(obj.p,obj.refLla); obj.rEcef=lla2ecef(obj.lla);
            obj.fnLast=dvSpecific/dt;
        end
        obj.v=vv; obj.q=qNew; obj.C=Cnew;
        obj.prevDtheta=dtheta; obj.prevDv=dv;
    end

    function correctState(obj,dp,dv,dphi)
        obj.p=obj.p+dp(:); obj.v=obj.v+dv(:);
        obj.lla=ned2lla(obj.p,obj.refLla); obj.rEcef=lla2ecef(obj.lla);
        correctedC=(eye(3)-skew(dphi(:)))*obj.C;
        obj.q=dcm2quat(correctedC); obj.C=quat2dcm(obj.q);
    end

    function eul=eul(obj), eul=dcm2eul(obj.C); end

    function s=getState(obj)
        s=struct('p',obj.p,'v',obj.v,'q',obj.q,'C',obj.C,'lla',obj.lla, ...
            'rEcef',obj.rEcef,'grav',obj.grav,'fnLast',obj.fnLast, ...
            'prevDtheta',obj.prevDtheta,'prevDv',obj.prevDv);
    end

    function setState(obj,s)
        fn=fieldnames(s);
        for i=1:numel(fn), obj.(fn{i})=s.(fn{i}); end
    end
end
end
