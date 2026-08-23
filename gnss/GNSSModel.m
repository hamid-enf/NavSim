classdef GNSSModel < handle
%GNSSMODEL Synthetic GNSS receiver with rate, noise, bias, scheduled and
% random dropouts, outliers and measurement delay.
%
% [hasMeas, z, evt] = update(obj, t, truth) is polled every engine step.
%   z.p, z.v : NED measurement
%   z.R, z.Rv: measurement covariance
%   evt      : '' | 'MEAS' | 'MEAS_OUTLIER' | 'DROPOUT'  (per GNSS epoch)

properties
    cfg
    nextEpoch = 0
    queue = {}            % delayed measurement queue (FIFO of structs)
    lastZ = []
    ndx = 0
    windows = zeros(0,2)  % dropout windows [t1 t2; ...]
    lastRate = nan
    lastEnabled = false
    gmState = zeros(3,1)  % Gauss-Markov correlated error state [m]
    gmInit = false        % true after the state is drawn from N(0, gmSigma)
    lastGmT = 0           % wall time of the last GM advance [s]
end

methods
    function updateParams(obj, cfg, tNow)
        oldRate = obj.lastRate;
        oldEnabled = obj.lastEnabled;
        newWindows = obj.parseWindows(cfg.GNSS.dropoutText); % validate before mutation
        obj.cfg = cfg;
        obj.windows = newWindows;
        obj.lastRate = max(cfg.GNSS.rate, 1e-3);
        obj.lastEnabled = logical(cfg.GNSS.enabled);

        if nargin >= 3
            if oldEnabled && ~obj.lastEnabled
                % Never deliver stale delayed measurements after re-enable.
                obj.queue = {};
            elseif ~oldEnabled && obj.lastEnabled
                obj.nextEpoch = tNow;  % immediate acquisition on re-enable
            elseif isfinite(oldRate) && abs(oldRate - obj.lastRate) > ...
                    10*eps(max([1, oldRate, obj.lastRate]))
                % Reschedule both rate increases and decreases from now.
                obj.nextEpoch = tNow + 1.0 / obj.lastRate;
            end
        end
    end

    function reset(obj)
        obj.nextEpoch = 0;
        obj.queue = {};
        obj.lastZ = [];
        obj.ndx = 0;
        obj.gmState = zeros(3,1);
        obj.gmInit = false;
        obj.lastGmT = 0;
    end

    function w = parseWindows(~, txt)
        w = zeros(0,2);
        if isstring(txt) && isscalar(txt), txt = char(txt); end
        if ~ischar(txt)
            error('NavSim:InvalidDropoutWindows', 'GNSS.dropoutText must be text.');
        end
        if isempty(strtrim(txt)), return; end
        segs = strsplit(txt, ';');
        for i = 1:numel(segs)
            seg = strtrim(segs{i});
            if isempty(seg), continue; end
            v = sscanf(seg, '%f');
            numericForm = ~isempty(regexp(seg, ...
                '^[-+]?\d*\.?\d+([eE][-+]?\d+)?\s+[-+]?\d*\.?\d+([eE][-+]?\d+)?$', 'once'));
            if numel(v) ~= 2 || ~numericForm || any(~isfinite(v)) || v(1) < 0 || v(2) < v(1)
                error('NavSim:InvalidDropoutWindows', ...
                    'Invalid GNSS dropout window "%s"; expected "start end" with 0 <= start <= end.', seg);
            end
            w(end+1, :) = [v(1) v(2)]; %#ok<AGROW>
        end
    end

    function tf = inDropout(obj, t)
        tf = false;
        c = obj.cfg;
        if c.GNSS.useDropout
            for i = 1:size(obj.windows, 1)
                if t >= obj.windows(i,1) && t <= obj.windows(i,2)
                    tf = true; return;
                end
            end
        end
        if c.GNSS.useDropout && c.GNSS.randDropProb > 0
            if rand < c.GNSS.randDropProb, tf = true; end
        end
    end

    function g = advanceGm(obj, t, c)
        %ADVANCEGM Stationary Gauss-Markov correlated error (multipath-like).
        % The state follows x' = exp(-dt/tau)*x + sigma*sqrt(1-exp(-2dt/tau))*w
        % and is drawn from the stationary distribution N(0, gmSigma) at the
        % first epoch.  Deliberately NOT reflected in R: modelling mismatch
        % (overconfident filter vs correlated reality) is the demonstration.
        if ~obj.gmInit
            obj.gmState = c.GNSS.gmSigma * randn(3,1);
            obj.gmInit = true;
        else
            dt = max(t - obj.lastGmT, 0);
            phi = exp(-dt / c.GNSS.gmTau);
            sig = c.GNSS.gmSigma * sqrt(max(1 - phi^2, 0));
            obj.gmState = phi * obj.gmState + sig * randn(3,1);
        end
        obj.lastGmT = t;
        g = obj.gmState;
    end

    function [hasMeas, z, evt] = update(obj, t, truth)
        hasMeas = false;  z = [];  evt = '';
        c = obj.cfg;
        if ~c.GNSS.enabled, return; end

        % --- new measurement epoch? ---
        if t >= obj.nextEpoch - 1e-12
            rate = max(c.GNSS.rate, 1e-3);
            obj.nextEpoch = obj.nextEpoch + 1.0 / rate;
            if obj.nextEpoch < t   % rate changed at runtime: resync schedule
                obj.nextEpoch = t + 1.0 / rate;
            end
            if obj.inDropout(t)
                evt = 'DROPOUT';
            else
                sH = c.GNSS.posSigmaH * double(c.GNSS.useNoise);
                sV = c.GNSS.posSigmaV * double(c.GNSS.useNoise);
                pmeas = truth.p + c.GNSS.biasNed(:) + [sH*randn; sH*randn; sV*randn];
                if c.GNSS.useGmNoise
                    pmeas = pmeas + obj.advanceGm(t, c);
                end
                isOut = false;
                if c.GNSS.useOutlier && rand < c.GNSS.outlierProb
                    pmeas = pmeas + c.GNSS.outlierMag * (2*rand(3,1) - 1);
                    isOut = true;
                end
                zs.p  = pmeas;
                zs.R  = diag([max(sH,0.05)^2, max(sH,0.05)^2, max(sV,0.05)^2]);
                zs.outlier = isOut;
                zs.tMeas = t;                 % physical measurement epoch
                zs.tEmit = t + c.GNSS.delay;  % receiver delivery epoch
                if isfield(truth,'lla'), zs.lla=truth.lla; else, zs.lla=[]; end
                zs.hasVel = c.GNSS.enableVel;
                if c.GNSS.enableVel
                    sVel = c.GNSS.velSigma * double(c.GNSS.useNoise);
                    zs.v  = truth.v + sVel * randn(3,1);
                    if isOut && c.GNSS.outlierVelSigma > 0
                        zs.v = zs.v + c.GNSS.outlierVelSigma * (2*rand(3,1) - 1);
                    end
                    zs.Rv = eye(3) * max(sVel, 0.01)^2;
                else
                    zs.v = []; zs.Rv = [];
                end
                obj.queue{end+1} = zs;
                evt = ternary(isOut, 'MEAS_OUTLIER', 'MEAS');
            end
        end

        % --- deliver delayed measurements ---
        if ~isempty(obj.queue)
            zq = obj.queue{1};
            if zq.tEmit <= t + 1e-12
                obj.queue(1) = [];
                hasMeas = true;
                z = zq;
                obj.lastZ = zq;
                obj.ndx = obj.ndx + 1;
            end
        end
    end
end
end

function out = ternary(cond, a, b)
if cond, out = a; else, out = b; end
end
