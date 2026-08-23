classdef IMUModel < handle
%IMUMODEL Configurable inertial sensor error model.
% Supports constant/Gauss-Markov or random-walk bias, white noise, scale
% factor, cross-axis misalignment, gyro g-sensitivity, saturation and
% quantization.  Rates/specific force are returned in SI units.

properties
    cfg
    Mg = eye(3)
    Ma = eye(3)
    bgBase = zeros(3,1)
    baBase = zeros(3,1)
    bgRW = zeros(3,1)
    baRW = zeros(3,1)
end

methods
    function updateParams(obj, cfg)
        obj.cfg = cfg;
        if cfg.IMU.useGyroBias
            obj.bgBase = deg2rad(cfg.IMU.gyroBiasDps(:));
        else
            obj.bgBase = zeros(3,1); obj.bgRW = zeros(3,1);
        end
        if cfg.IMU.useAccelBias
            obj.baBase = cfg.IMU.accelBiasMg(:)*1e-3*9.80665;
        else
            obj.baBase = zeros(3,1); obj.baRW = zeros(3,1);
        end
        if cfg.IMU.useGyroSF, Sg = diag(1+cfg.IMU.gyroSFPpm(:)*1e-6); else, Sg = eye(3); end
        if cfg.IMU.useAccelSF, Sa = diag(1+cfg.IMU.accelSFPpm(:)*1e-6); else, Sa = eye(3); end
        if cfg.IMU.useGyroMis, Gm = eye(3)+skew(deg2rad(cfg.IMU.gyroMisDeg(:))); else, Gm = eye(3); end
        if cfg.IMU.useAccelMis, Am = eye(3)+skew(deg2rad(cfg.IMU.accelMisDeg(:))); else, Am = eye(3); end
        obj.Mg = Gm*Sg; obj.Ma = Am*Sa;
    end

    function reset(obj)
        obj.bgRW = zeros(3,1); obj.baRW = zeros(3,1);
    end

    function [wm,fm,dbg] = measure(obj,wTrue,fTrue,dt)
        c = obj.cfg; I = c.IMU;
        if I.useGyroBias && I.gyroBiasRW > 0
            obj.bgRW = obj.advanceBias(obj.bgRW,deg2rad(I.gyroBiasRW),I.gyroBiasTau,dt,I.biasModel);
        end
        if I.useAccelBias && I.accelBiasRW > 0
            obj.baRW = obj.advanceBias(obj.baRW,I.accelBiasRW,I.accelBiasTau,dt,I.biasModel);
        end
        bg = obj.bgBase+obj.bgRW; ba = obj.baBase+obj.baRW;
        if I.useGyroNoise
            ng = deg2rad(I.gyroARWDpsHz)/sqrt(dt)*randn(3,1);
        else
            ng = zeros(3,1);
        end
        if I.useAccelNoise
            na = I.accelVRW/sqrt(dt)*randn(3,1);
        else
            na = zeros(3,1);
        end
        gSense = deg2rad(I.gyroGSensitivity(:)).*(fTrue(:)/9.80665);
        wmRaw = obj.Mg*wTrue(:)+bg+ng+gSense;
        fmRaw = obj.Ma*fTrue(:)+ba+na;
        wLim = deg2rad(I.gyroSaturationDps);
        fLim = I.accelSaturationG*9.80665;
        wm = max(-wLim,min(wLim,wmRaw));
        fm = max(-fLim,min(fLim,fmRaw));
        if I.gyroQuantizationDps > 0
            q = deg2rad(I.gyroQuantizationDps); wm = round(wm/q)*q;
        end
        if I.accelQuantization > 0
            q = I.accelQuantization; fm = round(fm/q)*q;
        end
        dbg = struct('bg',bg,'ba',ba,'ng',ng,'na',na,'gSense',gSense, ...
            'gyroSaturated',any(abs(wmRaw)>wLim),'accelSaturated',any(abs(fmRaw)>fLim));
    end
end

methods (Static, Access=private)
    function x = advanceBias(x,q,tau,dt,model)
        if strcmp(model,'gaussmarkov')
            phi = exp(-dt/tau);
            sigma = q*sqrt(0.5*tau*(1-phi^2));
            x = phi*x+sigma*randn(3,1);
        else
            x = x+q*sqrt(dt)*randn(3,1);
        end
    end
end
end
