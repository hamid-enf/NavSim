classdef BaroModel < handle
%BAROMODEL Synthetic barometric altimeter for altitude aiding.
%
%   [hasMeas, z] = update(obj, t, hTrue) is polled every engine step.
%     z.h : altitude measurement [m] (WGS84 height)
%     z.R : measurement variance [m^2]
%
% The model adds a constant bias, optional Gauss-Markov pressure drift
% (advanced with the exact stationary transition) and white noise.  Like
% GNSSModel, correlated drift is deliberately not reflected in R.

properties
    cfg
    nextEpoch = 0
    gmState = 0
    gmInit = false
    lastGmT = 0
end

methods
    function updateParams(obj, cfg)
        obj.cfg = cfg;
    end

    function reset(obj)
        obj.nextEpoch = 0;
        obj.gmState = 0;
        obj.gmInit = false;
        obj.lastGmT = 0;
    end

    function g = advanceGm(obj, t, c)
        %ADVANCEGM Stationary first-order Gauss-Markov pressure drift [m].
        if ~obj.gmInit
            obj.gmState = c.Baro.gmSigma * randn;
            obj.gmInit = true;
        else
            dt = max(t - obj.lastGmT, 0);
            phi = exp(-dt / c.Baro.gmTau);
            sig = c.Baro.gmSigma * sqrt(max(1 - phi^2, 0));
            obj.gmState = phi * obj.gmState + sig * randn;
        end
        obj.lastGmT = t;
        g = obj.gmState;
    end

    function [hasMeas, z] = update(obj, t, hTrue)
        hasMeas = false;  z = [];
        c = obj.cfg;
        if isempty(c) || ~c.Baro.enabled, return; end

        % --- new measurement epoch? ---
        if t >= obj.nextEpoch - 1e-12
            rate = max(c.Baro.rate, 1e-3);
            obj.nextEpoch = obj.nextEpoch + 1.0 / rate;
            if obj.nextEpoch < t   % rate changed at runtime: resync schedule
                obj.nextEpoch = t + 1.0 / rate;
            end
            drift = 0;
            if c.Baro.gmSigma > 0
                drift = obj.advanceGm(t, c);
            end
            sig = c.Baro.sigma;
            z = struct('h', hTrue + c.Baro.bias + drift + sig*randn, ...
                       'R', max(sig, 0.05)^2, 'tMeas', t);
            hasMeas = true;
        end
    end
end
end
