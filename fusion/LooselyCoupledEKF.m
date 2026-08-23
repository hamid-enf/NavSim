classdef LooselyCoupledEKF < handle
%LOOSELYCOUPLEDEKF Closed-loop 15-state error-state GNSS/INS filter.
% Includes WGS84 Earth/transport/Coriolis terms, third-order state
% transition with PSD quadrature noise, Gauss-Markov biases and NIS gating.
% Error convention is true-minus-estimate.

properties
    x=zeros(15,1)
    P=zeros(15)
    cfg
    initialized=false
    lastInnov=zeros(3,1)
    lastNIS=0
    lastRawNIS=0
    lastAccepted=true
    lastGate=inf
    rejectedCount=0
    acceptedCount=0
end

methods
    function updateParams(obj,cfg), obj.cfg=cfg; end

    function initState(obj,cfg)
        s=cfg.Fusion;
        sig=[ones(3,1)*s.p0pos;ones(3,1)*s.p0vel; ...
            ones(3,1)*deg2rad(s.p0attDeg);ones(3,1)*deg2rad(s.p0gyroBiasDps); ...
            ones(3,1)*s.p0accelBias];
        obj.P=diag(sig.^2); obj.x=zeros(15,1); obj.cfg=cfg;
        obj.lastInnov=zeros(3,1); obj.lastNIS=0; obj.lastRawNIS=0;
        obj.lastAccepted=true; obj.lastGate=inf;
        obj.rejectedCount=0; obj.acceptedCount=0; obj.initialized=true;
    end

    function Phi=predict(obj,C,fb,dt,cfg,lla,v)
        if ~obj.initialized, obj.initState(cfg); end
        obj.cfg=cfg; s=cfg.Fusion; fn=C*fb(:);
        if nargin<6 || isempty(lla), lla=[cfg.INS.refLat;cfg.INS.refLon;cfg.INS.refH]; end
        if nargin<7 || isempty(v), v=zeros(3,1); end
        Fc=zeros(15);
        Fc(4:6,7:9)=skew(fn); Fc(4:6,13:15)=-C;
        Fc(7:9,10:12)=C;
        if strcmp(cfg.INS.earthModel,'wgs84')
            % Position errors are reference-NED ECEF chords, while velocity
            % errors are resolved in the current local NED frame.
            Cref=nedRotation([cfg.INS.refLat;cfg.INS.refLon;cfg.INS.refH]);
            Ccur=nedRotation(lla); Fc(1:3,4:6)=Cref*Ccur';
            [wie,wen,win]=earthRatesNED(lla,v,cfg);
            if cfg.INS.useCoriolis
                lat=deg2rad(lla(1)); [RM,RN]=earthRadii(lat); h=lla(3);
                Aen=[0,1/(RN+h),0;-1/(RM+h),0,0;0,-tan(lat)/(RN+h),0];
                if ~cfg.INS.useTransportRate, Aen(:)=0; end
                Fc(4:6,4:6)=-skew(2*wie+wen)+skew(v)*Aen;
            end
            Fc(7:9,7:9)=-skew(win);
            Fc(6,3)=3.086e-6; % vertical free-air gravity gradient
        else
            Fc(1:3,4:6)=eye(3);
        end
        if strcmp(cfg.IMU.biasModel,'gaussmarkov')
            Fc(10:12,10:12)=-eye(3)/cfg.IMU.gyroBiasTau;
            Fc(13:15,13:15)=-eye(3)/cfg.IMU.accelBiasTau;
        end
        A=Fc*dt;
        qa=(s.qa*s.qScale)^2; qg=(deg2rad(s.qg)*s.qScale)^2;
        qbg=(deg2rad(s.qbg)*s.qScale)^2; qba=(s.qba*s.qScale)^2;
        if strcmp(cfg.INS.earthModel,'wgs84') || strcmp(cfg.IMU.biasModel,'gaussmarkov')
            % Third-order continuous-to-discrete integration.  Unlike the
            % legacy block approximation this carries sensor/bias driving
            % noise through all coupled error dynamics and cross terms.
            A2=A*A; Phi=eye(15)+A+0.5*A2+(A2*A)/6;
            Qc=zeros(15); Qc(4:6,4:6)=eye(3)*qa;
            Qc(7:9,7:9)=eye(3)*qg; Qc(10:12,10:12)=eye(3)*qbg;
            Qc(13:15,13:15)=eye(3)*qba;
            % Two-point Gauss-Legendre integration of exp(F*t)Qc exp(F*t)'.
            % This is fourth-order accurate and remains positive semidefinite.
            Qd=zeros(15); u=sqrt(3)/6;
            for alpha=[0.5-u,0.5+u]
                At=Fc*(alpha*dt); At2=At*At;
                B=eye(15)+At+0.5*At2+(At2*At)/6;
                Qd=Qd+(dt/2)*(B*Qc*B');
            end
            Qd=0.5*(Qd+Qd');
        else
            % Original flat-Earth discretization retained as a selectable
            % compatibility path for existing scenarios and teaching labs.
            Phi=eye(15)+A+0.5*(A*A);
            Qd=zeros(15);
            Qd(1:3,1:3)=eye(3)*qa*dt^3/3;
            Qd(1:3,4:6)=eye(3)*qa*dt^2/2; Qd(4:6,1:3)=Qd(1:3,4:6)';
            Qd(4:6,4:6)=eye(3)*qa*dt; Qd(7:9,7:9)=eye(3)*qg*dt;
            Qd(10:12,10:12)=eye(3)*qbg*dt; Qd(13:15,13:15)=eye(3)*qba*dt;
        end
        obj.x=Phi*obj.x;
        obj.P=Phi*obj.P*Phi'+Qd; obj.P=0.5*(obj.P+obj.P');
    end

    function accepted=updatePos(obj,zp,R)
        H=[eye(3),zeros(3,12)];
        accepted=obj.kalman(zp,H,R*obj.cfg.Fusion.rScale,obj.cfg.Fusion.nisGatePos);
    end

    function accepted=updateVel(obj,zv,Rv)
        H=[zeros(3,3),eye(3),zeros(3,9)];
        accepted=obj.kalman(zv,H,Rv*obj.cfg.Fusion.rScale,obj.cfg.Fusion.nisGateVel);
    end

    function accepted=kalman(obj,z,H,R,gate)
        innov=z(:)-H*obj.x; S=H*obj.P*H'+R;
        rawNIS=real(innov'*(S\innov)); mode=obj.cfg.Fusion.robustMode;
        accepted=true; Ruse=R;
        if ~strcmp(mode,'off') && rawNIS>gate
            if strcmp(mode,'adaptive')
                inflation=rawNIS/gate;
                if inflation<=obj.cfg.Fusion.maxRInflation
                    Ruse=R*inflation; S=H*obj.P*H'+Ruse;
                else
                    accepted=false;
                end
            else
                accepted=false;
            end
        end
        obj.lastInnov=innov; obj.lastRawNIS=rawNIS; obj.lastGate=gate;
        obj.lastAccepted=accepted;
        if ~accepted
            obj.lastNIS=rawNIS; obj.rejectedCount=obj.rejectedCount+1; return;
        end
        obj.lastNIS=real(innov'*(S\innov));
        K=(obj.P*H')/S; obj.x=obj.x+K*innov;
        IKH=eye(15)-K*H;
        obj.P=IKH*obj.P*IKH'+K*Ruse*K'; obj.P=0.5*(obj.P+obj.P');
        obj.acceptedCount=obj.acceptedCount+1;
    end

    function dx=consumeDx(obj)
        dx=obj.x;
        % Covariance reset Jacobian for closed-loop attitude injection.
        G=eye(15); G(7:9,7:9)=eye(3)-0.5*skew(dx(7:9));
        obj.P=G*obj.P*G'; obj.P=0.5*(obj.P+obj.P');
        obj.x(:)=0;
    end

    function s=sigmas(obj), s=sqrt(max(diag(obj.P),0)); end

    function s=getState(obj)
        s=struct('x',obj.x,'P',obj.P,'cfg',obj.cfg,'initialized',obj.initialized, ...
            'lastInnov',obj.lastInnov,'lastNIS',obj.lastNIS,'lastRawNIS',obj.lastRawNIS, ...
            'lastAccepted',obj.lastAccepted,'lastGate',obj.lastGate, ...
            'rejectedCount',obj.rejectedCount,'acceptedCount',obj.acceptedCount);
    end

    function setState(obj,s)
        fn=fieldnames(s);
        for i=1:numel(fn), obj.(fn{i})=s.(fn{i}); end
    end
end
end
