classdef PlotManager < handle
%PLOTMANAGER Builds and updates all 2D plot tabs inside a uitabgroup.
% Traces: Truth (black), INS (blue), GNSS (orange dots), Fused (green).

properties
    tg
    axPos = gobjects(0)
    lnPos = {}
    axVel = gobjects(0)
    lnVel = {}
    axAtt = gobjects(0)
    lnAtt = {}
    axErr = gobjects(0)
    lnErr = {}
    axSen = gobjects(0)
    lnSen = {}
    axMap = gobjects(1)
    lnMap = {}
    cTruth = [0 0 0]
    cIns = [0.20 0.45 0.85]
    cGnss = [0.90 0.40 0.10]
    cFus = [0.05 0.60 0.25]
    bgOverlays = {}
end

methods
    function build(obj, parent)
        % parent: uigridlayout cell host (tabgroup fills it automatically)
        obj.tg = uitabgroup(parent);

        % ---------------- Position tab ----------------
        tp = uitab(obj.tg, 'Title', 'Position');
        gl = uigridlayout(tp, [1 3]); gl.ColumnWidth = {'2x','2x','1x'};
        sub = uigridlayout(gl, [3 1]); sub.RowHeight = {'1x','1x','1x'};
        [obj.axPos, obj.lnPos] = obj.seriesGrid(sub, {'North [m]','East [m]','Down [m]'}, true);
        legend(obj.axPos(1), 'Location', 'northeast');
        mp = uigridlayout(gl, [1 1]); mp.Layout.Row = 1; mp.Layout.Column = [2 3];
        obj.axMap = uiaxes(mp);
        title(obj.axMap, 'Top view (map)'); xlabel(obj.axMap,'East [m]'); ylabel(obj.axMap,'North [m]');
        grid(obj.axMap,'on'); hold(obj.axMap,'on');
        obj.lnMap = { obj.mkLine(obj.axMap, obj.cTruth,'-',1.4,'Truth'), ...
                      obj.mkLine(obj.axMap, obj.cIns,'-',1.0,'INS'), ...
                      obj.mkLine(obj.axMap, obj.cGnss,'none',1,'GNSS'), ...
                      obj.mkLine(obj.axMap, obj.cFus,'-',1.2,'Fused') };
        set(obj.lnMap{3}, 'Marker','.', 'MarkerSize', 6);
        legend(obj.axMap, 'Location','northeast');
        axis(obj.axMap, 'equal');

        % ---------------- Velocity tab ----------------
        tv = uitab(obj.tg, 'Title', 'Velocity');
        g2 = uigridlayout(tv, [3 1]); g2.RowHeight = {'1x','1x','1x'};
        [obj.axVel, obj.lnVel] = obj.seriesGrid(g2, {'vN [m/s]','vE [m/s]','vD [m/s]'}, true);
        legend(obj.axVel(1), 'Location', 'northeast');

        % ---------------- Attitude tab ----------------
        ta = uitab(obj.tg, 'Title', 'Attitude');
        g3 = uigridlayout(ta, [3 1]); g3.RowHeight = {'1x','1x','1x'};
        [obj.axAtt, obj.lnAtt] = obj.seriesGrid(g3, {'Roll [deg]','Pitch [deg]','Yaw [deg]'}, false);
        for i = 1:3   % alignment-estimate trace (visible during the align phase)
            obj.lnAtt{i}{4} = obj.mkLine(obj.axAtt(i), [0.75 0.10 0.55], '--', 1.2, 'Align est');
        end
        legend(obj.axAtt(1), 'Location', 'northeast');

        % ---------------- Errors tab ----------------
        te = uitab(obj.tg, 'Title', 'Errors');
        g4 = uigridlayout(te, [2 2]); g4.RowHeight = {'1x','1x'}; g4.ColumnWidth = {'1x','1x'};
        obj.axErr = gobjects(4,1); obj.lnErr = cell(4,1);
        titles = {'Position error (norm)','Fused position error components', ...
                  'Velocity error (norm)','Attitude error (norm)'};
        ylab   = {'[m]','[m]','[m/s]','[deg]'};
        for i = 1:4
            obj.axErr(i) = uiaxes(g4); obj.axErr(i).Layout.Row = ceil(i/2);
            obj.axErr(i).Layout.Column = mod(i-1,2)+1;
            grid(obj.axErr(i),'on'); hold(obj.axErr(i),'on');
            title(obj.axErr(i), titles{i}); ylabel(obj.axErr(i), ylab{i}); xlabel(obj.axErr(i),'t [s]');
        end
        obj.lnErr{1} = { obj.mkLine(obj.axErr(1), obj.cIns,'-',1,'INS'), ...
                         obj.mkLine(obj.axErr(1), obj.cFus,'-',1.4,'Fused') };
        obj.lnErr{2} = { obj.mkLine(obj.axErr(2), [0.8 0.1 0.1],'-',1,'N'), ...
                         obj.mkLine(obj.axErr(2), [0.1 0.6 0.1],'-',1,'E'), ...
                         obj.mkLine(obj.axErr(2), [0.1 0.1 0.8],'-',1,'D') };
        obj.lnErr{3} = { obj.mkLine(obj.axErr(3), obj.cIns,'-',1,'INS'), ...
                         obj.mkLine(obj.axErr(3), obj.cFus,'-',1.4,'Fused') };
        obj.lnErr{4} = { obj.mkLine(obj.axErr(4), obj.cIns,'-',1,'INS'), ...
                         obj.mkLine(obj.axErr(4), obj.cFus,'-',1.4,'Fused') };
        legend(obj.axErr(1)); legend(obj.axErr(2)); legend(obj.axErr(3)); legend(obj.axErr(4));

        % ---------------- Sensors tab ----------------
        ts = uitab(obj.tg, 'Title', 'Sensors');
        g5 = uigridlayout(ts, [3 2]); g5.RowHeight = {'1x','1x','1x'};
        g5.ColumnWidth = {'1x','1x'};
        obj.axSen = gobjects(6,1); obj.lnSen = cell(6,1);
        lab = {'Gyro X [deg/s]','Gyro Y [deg/s]','Gyro Z [deg/s]', ...
               'Accel X [m/s^2]','Accel Y [m/s^2]','Accel Z [m/s^2]'};
        for i = 1:6
            obj.axSen(i) = uiaxes(g5);
            obj.axSen(i).Layout.Row = mod(i-1,3)+1;
            obj.axSen(i).Layout.Column = ceil(i/3);  % gyros col1, accels col2
        end
        % reorder: rows are X,Y,Z — fix layout explicitly
        for r = 1:3
            obj.axSen(r).Layout.Row = r;   obj.axSen(r).Layout.Column = 1;
            obj.axSen(r+3).Layout.Row = r; obj.axSen(r+3).Layout.Column = 2;
        end
        for i = 1:6
            grid(obj.axSen(i),'on'); hold(obj.axSen(i),'on');
            title(obj.axSen(i), lab{i}); xlabel(obj.axSen(i),'t [s]');
            lnT = obj.mkLine(obj.axSen(i), [0.55 0.55 0.55],'-',1.2,'True');
            lnM = obj.mkLine(obj.axSen(i), [0.75 0.10 0.35],'-',0.7,'Meas');
            obj.lnSen{i} = {lnT, lnM};
        end
        legend(obj.axSen(1));
        drawnow;
    end

    function [axs, lns] = seriesGrid(obj, parent, ylab, withGnss)
        n = numel(ylab);
        axs = gobjects(n,1); lns = cell(n,1);
        for i = 1:n
            axs(i) = uiaxes(parent); axs(i).Layout.Row = i;
            grid(axs(i),'on'); hold(axs(i),'on');
            ylabel(axs(i), ylab{i}); xlabel(axs(i), 't [s]');
            if withGnss
                lns{i} = { obj.mkLine(axs(i), obj.cTruth,'-',1.4,'Truth'), ...
                           obj.mkLine(axs(i), obj.cIns,'-',1.0,'INS'), ...
                           obj.mkLine(axs(i), obj.cGnss,'none',1,'GNSS'), ...
                           obj.mkLine(axs(i), obj.cFus,'-',1.2,'Fused') };
                set(lns{i}{3}, 'Marker','.', 'MarkerSize', 6);
            else
                lns{i} = { obj.mkLine(axs(i), obj.cTruth,'-',1.4,'Truth'), ...
                           obj.mkLine(axs(i), obj.cIns,'-',1.0,'INS'), ...
                           obj.mkLine(axs(i), obj.cFus,'-',1.2,'Fused') };
            end
        end
    end

    function h = mkLine(~, ax, c, ls, lw, nm)
        h = plot(ax, nan, nan, 'LineStyle', ls, 'Color', c, 'LineWidth', lw, ...
                 'DisplayName', nm);
        if strcmp(ls, 'none'), h.Marker = '.'; end
    end

    function clearAll(obj)
        allLines = [obj.lnPos(:); obj.lnVel(:); obj.lnAtt(:); obj.lnErr(:); obj.lnSen(:); {obj.lnMap}'];
        for i = 1:numel(allLines)
            grp = allLines{i};
            if ~iscell(grp), grp = {grp}; end
            for j = 1:numel(grp)
                if isvalid(grp{j}), set(grp{j}, 'XData', nan, 'YData', nan); end
            end
        end
        obj.bgOverlays = {};
    end

    function update(obj, d)
        if d.n < 2, return; end
        idx = 1:max(1, floor(d.n/2500)):d.n;
        t = d.t(idx);
        for i = 1:3
            obj.setXY(obj.lnPos{i}, t, [d.truthP(i,idx); d.insP(i,idx); d.gnssP(i,idx); d.fusP(i,idx)]);
            obj.setXY(obj.lnVel{i}, t, [d.truthV(i,idx); d.insV(i,idx); d.gnssV(i,idx); d.fusV(i,idx)]);
            A = rad2deg([d.truthE(i,idx); d.insE(i,idx); d.fusE(i,idx); d.alignEst(i,idx)]);
            if i == 3, A = rad2deg(wrapPiCustom(deg2rad(A))); end
            obj.setXY(obj.lnAtt{i}, t, A);
        end
        obj.setXY(obj.lnMap, [d.truthP(2,idx); d.insP(2,idx); d.gnssP(2,idx); d.fusP(2,idx)], ...
                            [d.truthP(1,idx); d.insP(1,idx); d.gnssP(1,idx); d.fusP(1,idx)]);
        % errors
        ePI = sqrt(sum((d.insP - d.truthP).^2, 1));
        ePF = sqrt(sum((d.fusP - d.truthP).^2, 1));
        eVI = sqrt(sum((d.insV - d.truthV).^2, 1));
        eVF = sqrt(sum((d.fusV - d.truthV).^2, 1));
        eAI = rad2deg(sqrt(sum(wrapPi(d.insE - d.truthE).^2, 1)));
        eAF = rad2deg(sqrt(sum(wrapPi(d.fusE - d.truthE).^2, 1)));
        obj.setXY(obj.lnErr{1}, t, [ePI(idx); ePF(idx)]);
        obj.setXY(obj.lnErr{2}, t, (d.fusP(:,idx) - d.truthP(:,idx)));
        obj.setXY(obj.lnErr{3}, t, [eVI(idx); eVF(idx)]);
        obj.setXY(obj.lnErr{4}, t, [eAI(idx); eAF(idx)]);
        % sensors
        for i = 1:3
            obj.setXY(obj.lnSen{i},   t, rad2deg([d.gyroT(i,idx); d.gyroM(i,idx)]));
            obj.setXY(obj.lnSen{i+3}, t, [d.accT(i,idx); d.accM(i,idx)]);
        end
    end

    function setXY(~, lns, X, Y)
        % X: 1xN or MxN matched with lines; Y likewise (MxN, one row per line)
        if size(X,1) == 1, X = repmat(X, size(Y,1), 1); end
        for j = 1:numel(lns)
            set(lns{j}, 'XData', X(j,:), 'YData', Y(j,:));
        end
    end
end
end

function a = wrapPiCustom(a)
a = mod(a + pi, 2*pi) - pi;
end
