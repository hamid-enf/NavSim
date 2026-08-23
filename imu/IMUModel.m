classdef IMUModel < handle
%IMUMODEL Synthetic IMU: bias, noise (ARW/VRW), scale factor, misalignment,
% optional bias random walk. The gyro/accel bias master toggles control both
% constant and random-walk bias components; all sources update live.
%
% Measurement model (per axis, body frame):
%   gyro_meas  = Gg * gyro_true  + bg + ng
%   accel_meas = Ga * accel_true + ba + na
% with  G = (I + skew(misalignment)) * diag(1 + scaleFactor).

properties
    cfg          % last applied config struct
    Mg = eye(3)  % total gyro transform matrix
    Ma = eye(3)  % total accel transform matrix
    bgBase = zeros(3,1)   % constant gyro bias [rad/s]
    baBase = zeros(3,1)   % constant accel bias [m/s^2]
    bgRW = zeros(3,1)     % random-walk part, gyro
    baRW = zeros(3,1)     % random-walk part, accel
end

methods
    function updateParams(obj, cfg)
        obj.cfg = cfg;
        if cfg.IMU.useGyroBias
            obj.bgBase = deg2rad(cfg.IMU.gyroBiasDps(:));
        else
            obj.bgBase = zeros(3,1);
            obj.bgRW = zeros(3,1);  % master bias toggle also disables accumulated RW
        end
        if cfg.IMU.useAccelBias
            obj.baBase = cfg.IMU.accelBiasMg(:) * 1e-3 * 9.80665;
        else
            obj.baBase = zeros(3,1);
            obj.baRW = zeros(3,1);
        end

        Sg = eye(3);
        if cfg.IMU.useGyroSF,  Sg = diag(1 + cfg.IMU.gyroSFPpm(:)*1e-6); end
        if cfg.IMU.useAccelSF, Sa = diag(1 + cfg.IMU.accelSFPpm(:)*1e-6); else, Sa = eye(3); end
        if cfg.IMU.useGyroMis,  Gmis = eye(3) + skew(deg2rad(cfg.IMU.gyroMisDeg(:)));  else, Gmis  = eye(3); end
        if cfg.IMU.useAccelMis, Amis = eye(3) + skew(deg2rad(cfg.IMU.accelMisDeg(:))); else, Amis = eye(3); end
        obj.Mg = Gmis * Sg;
        obj.Ma = Amis * Sa;
    end

    function reset(obj)
        obj.bgRW = zeros(3,1);
        obj.baRW = zeros(3,1);
    end

    function [wm, fm, dbg] = measure(obj, wTrue, fTrue, dt)
        c = obj.cfg;
        % bias random walk
        if c.IMU.useGyroBias && c.IMU.gyroBiasRW > 0
            obj.bgRW = obj.bgRW + deg2rad(c.IMU.gyroBiasRW) * sqrt(dt) * randn(3,1);
        end
        if c.IMU.useAccelBias && c.IMU.accelBiasRW > 0
            obj.baRW = obj.baRW + c.IMU.accelBiasRW * sqrt(dt) * randn(3,1);
        end
        bg = obj.bgBase + obj.bgRW;
        ba = obj.baBase + obj.baRW;
        % white noise: sigma per sample = density / sqrt(dt)
        if c.IMU.useGyroNoise
            ng = deg2rad(c.IMU.gyroARWDpsHz) / sqrt(dt) * randn(3,1);
        else
            ng = zeros(3,1);
        end
        if c.IMU.useAccelNoise
            na = c.IMU.accelVRW / sqrt(dt) * randn(3,1);
        else
            na = zeros(3,1);
        end
        wm = obj.Mg * wTrue + bg + ng;
        fm = obj.Ma * fTrue + ba + na;
        dbg = struct('bg', bg, 'ba', ba, 'ng', ng, 'na', na);
    end
end
end
