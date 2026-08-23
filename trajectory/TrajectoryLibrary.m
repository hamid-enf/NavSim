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
        d = containers.Map();
        d('Straight')    = 'Straight and level flight at constant heading.';
        d('Circle')      = 'Constant-altitude circle (coordinated turn).';
        d('FigureEight') = 'Horizontal figure-eight (Lissajous).';
        d('Acceleration')= 'Straight flight with constant acceleration.';
        d('Climb')       = 'Straight flight with constant climb rate.';
        d('Descent')     = 'Straight flight with constant descent rate.';
        d('Turn')        = 'Straight leg, then constant-rate turn.';
        d('Combined3D')  = 'Circle with vertical oscillation and mean climb.';
        d('UserDefined') = 'User NED position expression p(t), numeric derivatives.';
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
                pv = @(t) deal( [V*t*cos(h0); V*t*sin(h0); -(max(alt - rc*t,5))], ...
                                [V*cos(h0);   V*sin(h0);   (alt-rc*t>5)*rc  ], ...
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
        T.desc = sprintf('%s: %s', type, dmap(type));
    end

    function fh = wrapAttitude(pv, h0, g)
        % Wrap a position/velocity/acceleration function with synthesized attitude.
        function eul = attOf(t)
            [~, v, a] = pv(t);
            Vh = hypot(v(1), v(2));
            if Vh > 0.5
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
        w  = deg2rad(P.turnRate);
        if abs(w) < 1e-9, w = 1e-9; end
        function [p, v, a] = f(t)
            if t <= T1
                p = [V*t*cos(h0); V*t*sin(h0); -alt];
                v = [V*cos(h0);   V*sin(h0);   0];
                a = [0; 0; 0];
            else
                tau = t - T1;   H = h0 + w*tau;
                p1  = [V*T1*cos(h0); V*T1*sin(h0)];
                p   = [p1(1) + V/w*(sin(H) - sin(h0));
                       p1(2) - V/w*(cos(H) - cos(h0));
                       -alt];
                v   = [V*cos(H); V*sin(H); 0];
                a   = [V*w*-sin(H); V*w*cos(H); 0];
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
