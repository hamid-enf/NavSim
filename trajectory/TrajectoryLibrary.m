classdef TrajectoryLibrary
%TRAJECTORYLIBRARY Factory of analytic truth trajectories.
% T = TrajectoryLibrary.make(type, P) returns a struct with:
%   T.fh   : function handle  truth = T.fh(t)
%            truth = struct('t',t,'p',..,'v',..,'a',..,'eul',..,'eulDot',..)
%            p,v,a in local NED [m, m/s, m/s^2], eul = [roll;pitch;yaw] [rad]
%   T.desc : human readable description
% Attitude is synthesized physically: yaw = velocity direction, pitch =
% flight-path angle, roll = coordinated-turn bank angle.

methods (Static)

    function types = list()
        types = {'Straight','Circle','FigureEight','Acceleration','Climb', ...
                 'Descent','Turn','Combined3D','UserDefined'};
    end

    function d = descriptions()
        % A plain struct keeps the graphics-free core usable in minimal
        % Octave builds where the containers package is not installed.
        d = struct();
        d.Straight    = 'Straight and level flight at constant heading.';
        d.Circle      = 'Constant-altitude circle (coordinated turn).';
        d.FigureEight = 'Horizontal figure-eight (Lissajous).';
        d.Acceleration= 'Straight flight with constant acceleration.';
        d.Climb       = 'Straight flight with constant climb rate.';
        d.Descent     = 'Straight flight with constant descent rate.';
        d.Turn        = 'Straight leg, smooth turn entry, then constant-rate turn.';
        d.Combined3D  = 'Circle with vertical oscillation and mean climb.';
        d.UserDefined = 'User NED position expression p(t), numeric derivatives.';
    end

    function T = make(type, P)
        g  = 9.80665;
        h0 = deg2rad(P.heading0);
        V  = P.speed;  R = max(P.radius, 1);  alt = P.alt0;
        switch type
            case 'Straight'
                pv = @(t) deal( [V*t*cos(h0); V*t*sin(h0); -alt], ...
                                [V*cos(h0);   V*sin(h0);   0   ], ...
                                [0; 0; 0] );
            case 'Circle'
                w = V / R;
                pv0 = @(t) deal( [R*sin(w*t);  R*(1-cos(w*t)); -alt], ...
                                 [V*cos(w*t);  V*sin(w*t);     0   ], ...
                                 [-V*w*sin(w*t); V*w*cos(w*t); 0   ] );
                pv = TrajectoryLibrary.rotateHorizontal(pv0, h0);
            case 'FigureEight'
                w = V / R;
                pv0 = @(t) deal( [R*sin(w*t);    (R/2)*sin(2*w*t); -alt], ...
                                 [V*cos(w*t);     V*cos(2*w*t);    0   ], ...
                                 [-V*w*sin(w*t); -2*V*w*sin(2*w*t); 0  ] );
                pv = TrajectoryLibrary.rotateHorizontal(pv0, h0);
            case 'Acceleration'
                a0 = P.accel;
                pv = @(t) deal( [(V*t+0.5*a0*t^2)*cos(h0); (V*t+0.5*a0*t^2)*sin(h0); -alt], ...
                                [(V+a0*t)*cos(h0);         (V+a0*t)*sin(h0);         0   ], ...
                                [a0*cos(h0);               a0*sin(h0);               0   ] );
            case 'Climb'
                rc = P.climbRate;
                pv = @(t) deal( [V*t*cos(h0); V*t*sin(h0); -(alt + rc*t)], ...
                                [V*cos(h0);   V*sin(h0);   -rc          ], ...
                                [0; 0; 0] );
            case 'Descent'
                rc = P.climbRate;
                % Do not clamp at an artificial ground altitude: a hard
                % clamp makes velocity jump to zero with no acceleration,
                % so even a perfect IMU can no longer reproduce Truth.
                pv = @(t) deal( [V*t*cos(h0); V*t*sin(h0); -alt + rc*t], ...
                                [V*cos(h0);   V*sin(h0);   rc         ], ...
                                [0; 0; 0] );
            case 'Turn'
                pv = TrajectoryLibrary.mkTurn(P, h0, V, alt, TrajectoryLibrary.getDur(P));
            case 'Combined3D'
                w = V / R;  rc = P.climbRate;
                pv0 = @(t) deal( [R*sin(w*t);  R*(1-cos(w*t)); -(alt + 30*sin(w*t) + rc*t)], ...
                                 [V*cos(w*t);  V*sin(w*t);     -(30*w*cos(w*t) + rc)      ], ...
                                 [-V*w*sin(w*t); V*w*cos(w*t);  30*w*w*sin(w*t)           ] );
                pv = TrajectoryLibrary.rotateHorizontal(pv0, h0);
            case 'UserDefined'
                pv = TrajectoryLibrary.mkUser(P.userExpr);
            otherwise
                error('TrajectoryLibrary:unknownType', 'Unknown type %s', type);
        end
        T.fh   = TrajectoryLibrary.wrapAttitude(pv, h0, g);
        dmap   = TrajectoryLibrary.descriptions();
        T.desc = sprintf('%s: %s', type, dmap.(type));
    end

    function fh = wrapAttitude(pv, h0, g)
        % Wrap a position/velocity/acceleration function with synthesized attitude.
        function eul = attOf(t)
            [~, v, a] = pv(t);
            Vh = hypot(v(1), v(2));
            % Preserve heading dynamics at low but nonzero speed.  Using the
            % old 0.5 m/s cutoff made a platform moving at exactly 0.5 m/s
            % report zero angular rate, so alignment could misclassify a
            % genuine turn as static.
            if Vh > 1e-6
                yaw   = atan2(v(2), v(1));
                pitch = atan2(-v(3), Vh);
                yd    = (v(1)*a(2) - v(2)*a(1)) / max(Vh*Vh, 1e-3);
                roll  = atan(Vh * yd / g);
                roll  = max(-1.0, min(1.0, roll)); % clamp ~ +/-57 deg
            else
                yaw   = h0;
                pitch = atan2(-v(3), 0.5);
                roll  = 0;
            end
            eul = [roll; pitch; yaw];
        end
        function s = fullTruth(t)
            [p, v, a] = pv(t);
            e  = attOf(t);
            hh = 1e-3;
            ep = attOf(t + hh); em = attOf(max(t - hh, 0));
            if t < hh, den = hh; dp = ep - e; else, den = 2*hh; dp = ep - em; end
            ed = wrapPi(dp) / den;
            s = struct('t',t,'p',p(:),'v',v(:),'a',a(:),'eul',e,'eulDot',ed);
        end
        fh = @fullTruth;
    end

    function d = getDur(P)
        if isfield(P, 'durationVal') && ~isempty(P.durationVal)
            d = P.durationVal;
        else
            d = 120;
        end
    end

    function pv = rotateHorizontal(pv0, heading)
        [~, v0, ~] = pv0(0);
        if hypot(v0(1), v0(2)) > 1e-12
            baseHeading = atan2(v0(2), v0(1));
        else
            baseHeading = 0;
        end
        ang = heading - baseHeading;
        R = [cos(ang), -sin(ang); sin(ang), cos(ang)];
        function [p, v, a] = f(t)
            [p, v, a] = pv0(t);
            p(1:2) = R * p(1:2);
            v(1:2) = R * v(1:2);
            a(1:2) = R * a(1:2);
        end
        pv = @f;
    end

    function pv = mkTurn(P, h0, V, alt, dur)
        T1 = 0.3 * dur;
        Tr = min(5, max(2, 0.2 * dur)); % smooth turn-entry duration [s]
        w  = deg2rad(P.turnRate);
        if abs(w) < 1e-9, w = 1e-9; end
        R0 = [cos(h0), -sin(h0); sin(h0), cos(h0)];
        function [p, v, a] = f(t)
            if t <= T1
                p = [V*t*cos(h0); V*t*sin(h0); -alt];
                v = [V*cos(h0);   V*sin(h0);   0];
                a = [0; 0; 0];
            else
                tau = t - T1;
                % Start from the exact circular arc, but ramp its lateral
                % displacement with a quintic smootherstep.  s, sdot and
                % sddot match [0,0,0] -> [1,0,0], making p/v/a C2 at both
                % ends and preventing an impossible instantaneous bank jump.
                u = min(max(tau / Tr, 0), 1);
                s = 10*u^3 - 15*u^4 + 6*u^5;
                if tau < Tr
                    sd  = (30*u^2 - 60*u^3 + 30*u^4) / Tr;
                    sdd = (60*u - 180*u^2 + 120*u^3) / (Tr^2);
                else
                    sd = 0; sdd = 0;
                end
                x = V/w * sin(w*tau);
                y0 = V/w * (1-cos(w*tau));
                vx = V*cos(w*tau);
                vy0 = V*sin(w*tau);
                ax = -V*w*sin(w*tau);
                ay0 = V*w*cos(w*tau);
                xy = [x; y0*s];
                vv = [vx; vy0*s + y0*sd];
                aa = [ax; ay0*s + 2*vy0*sd + y0*sdd];
                p1 = [V*T1*cos(h0); V*T1*sin(h0)];
                pn = p1 + R0 * xy;
                vn = R0 * vv;
                an = R0 * aa;
                p = [pn; -alt];
                v = [vn; 0];
                a = [an; 0];
            end
        end
        pv = @f;
    end

    function pv = mkUser(expr)
        pf = str2func(['@(t) (' expr ')']);
        q0 = pf(0);
        if numel(q0) ~= 3
            error('TrajectoryLibrary:badUser', ...
                'User expression must return a 3-element NED position.');
        end
        hh = 1e-2;
        function [p, v, a] = f(t)
            p  = pf(t); p = p(:);
            pp = pf(t + hh); pp = pp(:);
            pm = pf(max(t - hh, 0)); pm = pm(:);
            if t < hh
                ppp = pf(t + 2*hh); ppp = ppp(:);
                v = (pp - p)/hh;
                a = (ppp - 2*pp + p)/(hh*hh);
            else
                v = (pp - pm)/(2*hh);
                a = (pp - 2*p + pm)/(hh*hh);
            end
        end
        pv = @f;
    end
end
end
