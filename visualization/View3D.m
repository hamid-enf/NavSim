classdef View3D < handle
%VIEW3D 3D scene: vehicle (body axes), navigation axes, true/estimated
% trails and GNSS points, rendered in the local NED frame.

properties
    ax
    vehPatch
    bodyAx = gobjects(3,1)
    navL = gobjects(3,1)
    navT = gobjects(3,1)
    trailTrue
    trailEst
    gnssPts
    Vb               % vehicle template vertices (body frame)
    F                % patch faces
    scaleV = 10
    bounds = [-100 100 -100 100 -120 0]
    nTrailed = 0
end

methods
    function build(obj, parent)
        obj.ax = uiaxes(parent);
        hold(obj.ax, 'on'); grid(obj.ax, 'on');
        xlabel(obj.ax, 'N [m]'); ylabel(obj.ax, 'E [m]'); zlabel(obj.ax, 'D [m]');
        title(obj.ax, '3D View (local NED)');
        view(obj.ax, 3); axis(obj.ax, 'vis3d');
        daspect(obj.ax, [1 1 1]);

        % navigation-frame triad at origin (rescaled by setBounds)
        obj.navL = gobjects(3,1); obj.navT = gobjects(3,1);
        cols = [0.85 0.1 0.1; 0.1 0.6 0.1; 0.1 0.2 0.8];
        labs = {'N','E','D'};
        for i = 1:3
            obj.navL(i) = plot3(obj.ax, nan(1,2), nan(1,2), nan(1,2), ...
                'Color', cols(i,:), 'LineWidth', 2.5, 'HandleVisibility', 'off');
            obj.navT(i) = text(obj.ax, 0, 0, 0, labs{i}, 'Color', cols(i,:), ...
                'FontWeight', 'bold');
        end
        obj.updateNavTriad(30);

        % trails and GNSS points
        obj.trailTrue = animatedline(obj.ax, 'Color', [0 0 0], 'LineWidth', 1.5, ...
            'DisplayName', 'True trajectory');
        obj.trailEst = animatedline(obj.ax, 'Color', [0.05 0.6 0.25], 'LineWidth', 1.5, ...
            'DisplayName', 'Estimated trajectory');
        obj.gnssPts = animatedline(obj.ax, 'LineStyle', 'none', 'Marker', 'o', ...
            'MarkerSize', 4, 'Color', [0.9 0.4 0.1], 'DisplayName', 'GNSS');

        % vehicle: simple aircraft (body frame: x fwd, y right, z down)
        obj.Vb = [ 2.4  0    0    ;   % 1 nose
                  -1.6  0    0.15 ;   % 2 tail
                   0.2  1.8  0    ;   % 3 right wing
                   0.2 -1.8  0    ;   % 4 left wing
                  -1.4  0   -0.8  ;   % 5 fin tip
                  -1.55 0    0.55 ];  % 6 fin base
        obj.F = [1 3 2; 1 2 4; 2 5 6; 2 6 5];
        obj.vehPatch = patch(obj.ax, 'Vertices', zeros(6,3), 'Faces', obj.F, ...
            'FaceColor', [0.25 0.45 0.85], 'EdgeColor', 'k', 'LineWidth', 0.8, ...
            'DisplayName', 'Vehicle');
        for i = 1:3
            obj.bodyAx(i) = plot3(obj.ax, nan(1,2), nan(1,2), nan(1,2), 'LineWidth', 2);
        end
        obj.bodyAx(1).Color = [0.85 0.1 0.1];
        obj.bodyAx(2).Color = [0.1 0.6 0.1];
        obj.bodyAx(3).Color = [0.1 0.2 0.8];
        legend(obj.ax, 'Location', 'northeast');
    end

    function updateNavTriad(obj, L)
        D = [L 0 0; 0 L 0; 0 0 0.6*L];
        for i = 1:3
            set(obj.navL(i), 'XData', [0 D(i,1)], 'YData', [0 D(i,2)], 'ZData', [0 D(i,3)]);
            set(obj.navT(i), 'Position', 1.08 * D(i,:));
        end
    end

    function setBounds(obj, pts)
        mn = min(pts, [], 2); mx = max(pts, [], 2);
        pad = max(20, 0.15 * max(mx - mn));
        obj.bounds = [mn(1)-pad, mx(1)+pad, mn(2)-pad, mx(2)+pad, ...
                      min(-120, mn(3)-pad), max(0, mx(3)+pad)];
        span = max([mx(1)-mn(1), mx(2)-mn(2)]);
        obj.scaleV = max(span/35, 8);
        obj.updateNavTriad(max(30, span*0.10));
        obj.applyLimits();
    end

    function applyLimits(obj)
        b = obj.bounds;
        xlim(obj.ax, b(1:2)); ylim(obj.ax, b(3:4)); zlim(obj.ax, b(5:6));
    end

    function reset(obj)
        if isempty(obj.trailTrue) || ~isvalid(obj.trailTrue), return; end
        clearpoints(obj.trailTrue); clearpoints(obj.trailEst); clearpoints(obj.gnssPts);
        obj.nTrailed = 0;
    end

    function update(obj, d)
        % d: log slice; appends new points and updates the vehicle pose.
        if d.n < 1, return; end
        i0 = obj.nTrailed + 1;
        if i0 <= d.n
            idx = i0:d.n;
            addpoints(obj.trailTrue, d.truthP(1,idx), d.truthP(2,idx), d.truthP(3,idx));
            addpoints(obj.trailEst,  d.fusP(1,idx),   d.fusP(2,idx),   d.fusP(3,idx));
            gm = ~isnan(d.gnssFlag(idx));
            gi = idx(gm);
            if ~isempty(gi)
                addpoints(obj.gnssPts, d.gnssP(1,gi), d.gnssP(2,gi), d.gnssP(3,gi));
            end
            obj.nTrailed = d.n;
        end
        p   = d.truthP(:, d.n);
        eul = d.truthE(:, d.n);
        C   = eul2dcm(eul);
        Vw  = (C * (obj.Vb.' * obj.scaleV/10)).' + p.';
        set(obj.vehPatch, 'Vertices', Vw);
        L = obj.scaleV * 0.5;
        for i = 1:3
            tip = p + C(:, i) * L;
            set(obj.bodyAx(i), 'XData', [p(1) tip(1)], 'YData', [p(2) tip(2)], ...
                'ZData', [p(3) tip(3)]);
        end
    end
end
end
