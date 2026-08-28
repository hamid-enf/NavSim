classdef NavSimApp < handle
%NAVSIMAPP Interactive Navigation Simulator GUI (main application class).
%
%   app = NavSimApp;
%
% Left column : parameter tabs (Simulation..Errors, Experiments, Logs) +
%               transport controls (Start/Pause/Stop/Reset/Step, speed).
% Right column: plot tabs (Position, Velocity, Attitude, Errors, Sensors),
%               3D view, and the live Data Flow / Education monitor.

properties
    Fig
    cfg
    engine
    pm          % PlotManager
    v3d         % View3D
    dfv         % DataFlowView
    controls                % containers.Map: tag -> cell of control handles
    syncing = false
    tmr
    playing = false
    replaying = false
    replayData = []
    replayIdx = 1
    lastRefresh = 0
    realtimeBudget = 0       % accumulated simulated seconds allowed by wall-clock ticks
    dirtyNeedsReset = false
    % transport / status handles
    btnStart
    btnPause
    btnStep
    btnStop
    btnReset
    sldSpeed
    lblSpeed
    lblTime
    lblPhase
    lblGnss
    lblErr
    % experiments tab
    ddExp
    txtExpDesc
    tblExp
    axExp
    btnExpInfo
    % logs tab
    txtLog
    txtLogInfo
    btnReplay
    labels = containers.Map('KeyType','char','ValueType','any')
    baseLabel = containers.Map('KeyType','char','ValueType','any')
    baseColor = containers.Map('KeyType','char','ValueType','any')
    sldScrub
    lblScrub
end

methods
    function obj = NavSimApp()
        obj.cfg = defaultConfig();
        obj.engine = SimEngine(obj.cfg);
        obj.controls = containers.Map();
        obj.buildGUI();
        obj.syncUI();
        obj.resetViewBounds();
        obj.tmr = timer('ExecutionMode','fixedSpacing', 'Period', 0.05, ...
            'BusyMode','drop', 'TimerFcn', @(~,~) obj.tick());
        obj.logMsg('Simulator initialized. Press Start.');
    end

    % ============================================================ GUI build
    function buildGUI(obj)
        obj.Fig = uifigure('Name', 'Navigation Simulator — GNSS/INS Educational Lab', ...
            'Position', [30 30 1560 900], 'CloseRequestFcn', @(~,~) obj.closeApp());
        main = uigridlayout(obj.Fig, [1 2]);
        main.ColumnWidth = {380, '1x'};

        % ---------------- left column ----------------
        left = uigridlayout(main, [2 1]);
        left.RowHeight = {'1x', 200};
        ltg = uitabgroup(left);
        obj.buildSpecTabs(ltg);
        obj.buildExperimentsTab(ltg);
        obj.buildLogsTab(ltg);
        obj.buildTransport(left);

        % ---------------- right column ----------------
        right = uigridlayout(main, [2 1]);
        right.RowHeight = {'1x', 30};
        host = uigridlayout(right, [1 1]);
        obj.pm = PlotManager(); obj.pm.build(host);
        % 3D view tab
        t3 = uitab(obj.pm.tg, 'Title', '3D View');
        g3 = uigridlayout(t3, [1 1]); g3.Padding = [2 2 2 2];
        obj.v3d = View3D(); obj.v3d.build(g3);
        % data flow tab
        td = uitab(obj.pm.tg, 'Title', 'Data Flow');
        obj.dfv = DataFlowView(); obj.dfv.build(td);
        obj.buildStatusBar(right);
    end

    function buildSpecTabs(obj, ltg)
        spec = ParamCatalog();
        tabNames = unique(spec(:,1), 'stable');
        for t = 1:numel(tabNames)
            tn = tabNames{t};
            tab = uitab(ltg, 'Title', tn);
            rows = find(strcmp(spec(:,1), tn));
            g = uigridlayout(tab, [numel(rows) 2]);
            g.RowHeight = repmat({24}, 1, numel(rows));
            g.ColumnWidth = {'1.25x', '1x'};
            g.Scrollable = 'on';
            for j = 1:numel(rows)
                row = spec(rows(j), :);
                label = row{2}; tag = row{3}; typ = row{4}; extra = row{5};
                lab = uilabel(g, 'Text', label, 'HorizontalAlignment', 'right', 'FontSize', 10);
                llst = {};
                if isKey(obj.labels, tag), llst = obj.labels(tag); end
                llst{end+1} = lab; obj.labels(tag) = llst;
                blst = {};
                if isKey(obj.baseLabel, tag), blst = obj.baseLabel(tag); end
                blst{end+1} = label; obj.baseLabel(tag) = blst;
                clst = {};
                if isKey(obj.baseColor, tag), clst = obj.baseColor(tag); end
                clst{end+1} = lab.FontColor; obj.baseColor(tag) = clst;
                obj.makeControl(g, tag, typ, extra);
            end
        end
    end

    function makeControl(obj, g, tag, typ, extra)
        val = getByPath(obj.cfg, tag);
        switch typ
            case 'num'
                h = uieditfield(g, 'numeric', 'Value', val, 'Limits', extra(1:2), ...
                    'ValueChangedFcn', @(src,~) obj.onParam(tag, src.Value));
                if any(strcmp(tag, {'Sim.seed','Sim.chunkFast'}))
                    h.RoundFractionalValues = 'on';
                end
            case 'check'
                h = uicheckbox(g, 'Text', '', 'Value', logical(val), ...
                    'ValueChangedFcn', @(src,~) obj.onParam(tag, logical(src.Value)));
            case 'drop'
                h = uidropdown(g, 'Items', extra, 'Value', char(val), ...
                    'ValueChangedFcn', @(src,~) obj.onParam(tag, char(src.Value)));
            case 'text'
                h = uieditfield(g, 'text', 'Value', char(val), ...
                    'ValueChangedFcn', @(src,~) obj.onParam(tag, char(src.Value)));
        end
        h.FontSize = 10;
        if isKey(obj.controls, tag)
            lst = obj.controls(tag);
        else
            lst = {};
        end
        lst{end+1} = h;
        obj.controls(tag) = lst;
    end

    function buildTransport(obj, parent)
        p = uipanel(parent, 'Title', 'Transport');
        g = uigridlayout(p, [3 5]);
        g.RowHeight = {30, 26, '1x'};
        g.ColumnWidth = {'1x','1x','1x','1x','1x'};
        obj.btnStart = uibutton(g, 'push', 'Text', 'Start', ...
            'ButtonPushedFcn', @(~,~) obj.onStart(), 'FontWeight','bold', ...
            'BackgroundColor', [0.75 0.92 0.75]);
        obj.btnPause = uibutton(g, 'push', 'Text', 'Pause', 'ButtonPushedFcn', @(~,~) obj.onPause());
        obj.btnStop  = uibutton(g, 'push', 'Text', 'Stop',  'ButtonPushedFcn', @(~,~) obj.onStop());
        obj.btnReset = uibutton(g, 'push', 'Text', 'Reset', 'ButtonPushedFcn', @(~,~) obj.onReset());
        obj.btnStep  = uibutton(g, 'state', 'Text', 'Step', 'ValueChangedFcn', @(src,~) obj.onStep(src));
        uilabel(g, 'Text', 'Simulation speed:', 'HorizontalAlignment','right', 'FontSize',10);
        obj.sldSpeed = uislider(g, 'Limits', [0.1 20], 'Value', 1, ...
            'ValueChangedFcn', @(src,~) obj.onSpeed(src.Value));
        obj.sldSpeed.Layout.Column = [2 4];
        obj.lblSpeed = uilabel(g, 'Text', '1.0x', 'FontSize', 10);
        obj.lblTime = uilabel(g, 'Text', 't = 0.00 / 120 s', 'FontWeight', 'bold');
        obj.lblTime.Layout.Column = [1 5];
    end

    function buildStatusBar(obj, parent)
        g = uigridlayout(parent, [1 4]);
        g.ColumnWidth = {'1x','1x','1x','1.4x'};
        g.BackgroundColor = [0.92 0.92 0.95];
        obj.lblPhase = uilabel(g, 'Text', 'phase: idle');
        obj.lblGnss  = uilabel(g, 'Text', 'GNSS: -');
        obj.lblErr   = uilabel(g, 'Text', '|pos err| fused: -');
        obj.btnExpInfo = uilabel(g, 'Text', 'Ready.', ...
            'FontWeight', 'bold', 'FontColor', [0.1 0.35 0.1]);
    end

    function buildExperimentsTab(obj, ltg)
        tab = uitab(ltg, 'Title', 'Experiments');
        g = uigridlayout(tab, [7 1]);
        g.RowHeight = {26, '1.1x', 26, 26, 120, 110, '1x'};
        g.Scrollable = 'on';
        obj.ddExp = uidropdown(g, 'Items', ExperimentPresets.list(), ...
            'ValueChangedFcn', @(src,~) obj.onExpSelect(src));
        obj.txtExpDesc = uitextarea(g, 'Editable', 'off', 'FontSize', 10, 'Value', {''});
        uibutton(g, 'push', 'Text', 'Apply to Config (then Start to watch)', ...
            'ButtonPushedFcn', @(~,~) obj.onExpApply());
        uibutton(g, 'push', 'Text', 'Run Headless & Compare (instant)', ...
            'ButtonPushedFcn', @(~,~) obj.onExpRun(), ...
            'BackgroundColor', [0.78 0.85 0.98]);
        obj.axExp = uiaxes(g); title(obj.axExp, 'Position error norm'); grid(obj.axExp, 'on');
        obj.axExp.YScale = 'log';
        xlabel(obj.axExp, 't [s]'); ylabel(obj.axExp, '|pos err| [m]');
        hold(obj.axExp, 'on');
        obj.tblExp = uitable(g, 'ColumnName', {'Experiment','RMS pos [m]','Max pos [m]', ...
            'Final pos [m]','RMS att [deg]'}, 'RowName', {}, 'FontSize', 9);
        uilabel(g, 'Text', ['Experiments run the same graphics-free engine headless. ' ...
            'Apply-to-Config loads the preset into the live simulator.'], 'FontSize', 9);
        obj.onExpSelect(obj.ddExp);
    end

    function buildLogsTab(obj, ltg)
        tab = uitab(ltg, 'Title', 'Logs');
        g = uigridlayout(tab, [12 1]);
        g.RowHeight = {26, 26, 26, 26, 26, 26, 30, 4, 60, '1x', 4, 4};
        g.Scrollable = 'on';
        uibutton(g, 'push', 'Text', 'Save log MAT...', 'ButtonPushedFcn', @(~,~) obj.onSaveMat());
        uibutton(g, 'push', 'Text', 'Save log CSV...', 'ButtonPushedFcn', @(~,~) obj.onSaveCsv());
        uibutton(g, 'push', 'Text', 'Load MAT & view...', 'ButtonPushedFcn', @(~,~) obj.onLoadMat());
        obj.btnReplay = uibutton(g, 'push', 'Text', 'Replay animation', ...
            'ButtonPushedFcn', @(~,~) obj.onReplayToggle(), 'Enable', 'off');
        uibutton(g, 'push', 'Text', 'Save config preset...', ...
            'ButtonPushedFcn', @(~,~) obj.onSavePreset());
        uibutton(g, 'push', 'Text', 'Load config preset...', ...
            'ButtonPushedFcn', @(~,~) obj.onLoadPreset());
        uilabel(g, 'Text', 'Scrub loaded log (time position):', 'FontSize', 9);
        obj.sldScrub = uislider(g, 'Limits', [0 1], 'Value', 1, 'Enable', 'off', ...
            'ToolTip', 'Moves the plot cursor through a loaded log', ...
            'ValueChangedFcn', @(src,~) obj.onScrub(src.Value));
        obj.lblScrub = uilabel(g, 'Text', 'scrub: -', 'FontSize', 9);
        obj.txtLogInfo = uitextarea(g, 'Editable', 'off', 'FontSize', 9, 'Value', {'No log yet.'});
        obj.txtLog = uitextarea(g, 'Editable', 'off', 'FontSize', 9, ...
            'Value', {'--- event log ---'});
    end

    % ============================================================ UI utils
    function syncUI(obj)
        obj.syncing = true;
        ks = keys(obj.controls);
        for i = 1:numel(ks)
            tag = ks{i};
            val = getByPath(obj.cfg, tag);
            lst = obj.controls(tag);
            for j = 1:numel(lst)
                lst{j}.Value = val;  % control type matches the config value type
            end
        end
        if ~isempty(obj.sldSpeed) && isvalid(obj.sldSpeed)
            obj.sldSpeed.Value = obj.cfg.Sim.speed;
            obj.lblSpeed.Text = sprintf('%.1fx', obj.cfg.Sim.speed);
        end
        obj.syncing = false;
        obj.updateDirtyBadges();
    end

    function onParam(obj, tag, val)
        if obj.syncing, return; end
        oldCfg = obj.cfg;
        newCfg = setByPath(oldCfg, tag, val);
        rtFusion = startsWith(tag, 'Fusion.') && ~startsWith(tag, 'Fusion.p0');
        rtEngine = startsWith(tag, 'IMU.') || startsWith(tag, 'GNSS.') || ...
            startsWith(tag, 'GNSS2.') || startsWith(tag, 'Baro.') || rtFusion;
        rtUi = strcmp(tag, 'Sim.mode') || strcmp(tag, 'Sim.chunkFast');
        if rtEngine
            try
                obj.engine.applyRuntime(newCfg);
            catch ME
                obj.syncing = true;
                lst = obj.controls(tag);
                oldVal = getByPath(oldCfg, tag);
                for j = 1:numel(lst), lst{j}.Value = oldVal; end
                obj.syncing = false;
                obj.msg(['Rejected ' tag ': ' ME.message]);
                return;
            end
        end

        % Commit only after a runtime update succeeds, then synchronize any
        % duplicate controls (notably the Errors master toggles).
        obj.cfg = newCfg;
        obj.syncing = true;
        if isKey(obj.controls, tag)
            lst = obj.controls(tag);
            for j = 1:numel(lst), lst{j}.Value = val; end
        end
        obj.syncing = false;
        if rtEngine || rtUi
            obj.msg(['Runtime update: ' tag]);
        else
            obj.dirtyNeedsReset = true;
            obj.msg(['Pending (applies on Reset/Start): ' tag]);
        end
        obj.updateDirtyBadges();
        if startsWith(tag, 'Traj.') || strcmp(tag, 'Sim.duration')
            % update 3D bounds preview only when not running
            if ~obj.playing, obj.resetViewBounds(); end
        end
    end

    function msg(obj, s)
        obj.btnExpInfo.Text = s;
    end

    function logMsg(obj, s)
        v = obj.txtLog.Value;
        if ~iscell(v), v = {v}; end
        v{end+1} = sprintf('[%7.1f] %s', obj.engine.t, s);
        if numel(v) > 60, v = v(end-59:end); end
        obj.txtLog.Value = v;
    end

    function resetViewBounds(obj)
        try
            validateConfig(obj.cfg);
            p = obj.cfg.Traj;
            p.durationVal = obj.cfg.Sim.duration;
            trajPreview = TrajectoryLibrary.make(p.type, p);
            ts = linspace(0, obj.cfg.Sim.duration, 200);
            pts = zeros(3, numel(ts));
            for i = 1:numel(ts)
                q = trajPreview.fh(ts(i));
                pts(:,i) = q.p;
            end
            obj.v3d.setBounds(pts);
        catch ME
            obj.msg(['Trajectory error: ' ME.message]);
        end
    end

    % ============================================================ transport
    function onStart(obj)
        if obj.replaying, obj.onReplayToggle(); end
        if obj.dirtyNeedsReset || obj.engine.done
            try
                obj.engine.configure(obj.cfg);
            catch ME
                obj.msg(['Cannot start: ' ME.message]);
                obj.logMsg(['Configuration rejected: ' ME.message]);
                return;
            end
            obj.replayData = [];
            obj.btnReplay.Enable = 'off';
            obj.btnReplay.Text = 'Replay animation';
            obj.pm.clearAll(); obj.v3d.reset(); obj.resetViewBounds();
            obj.dirtyNeedsReset = false;
        end
        % A live run must never retain a MAT/previous-run replay payload or
        % its rendered trails.  This branch matters when a log was loaded
        % while the live engine was merely paused (no reconfigure above).
        if ~isempty(obj.replayData)
            obj.replayData = [];
            obj.btnReplay.Enable = 'off';
            obj.btnReplay.Text = 'Replay animation';
            obj.pm.clearAll(); obj.v3d.reset();
            try
                obj.v3d.setBounds(obj.engine.sampleTruth(200));
            catch ME
                obj.msg(['Could not restore live view: ' ME.message]);
                return;
            end
        end
        obj.sldScrub.Enable = 'off';
        obj.realtimeBudget = 0;
        obj.playing = true;
        obj.msg('Running...');
        if ~strcmp(obj.tmr.Running, 'on'), start(obj.tmr); end
    end

    function onPause(obj)
        obj.playing = false;
        obj.msg('Paused.');
    end

    function onStop(obj)
        obj.playing = false;
        obj.autoSavePreset();
        obj.msg('Stopped (data kept; Reset to restart).');
    end

    function onReset(obj)
        obj.playing = false; obj.replaying = false;
        try
            obj.engine.configure(obj.cfg);
        catch ME
            % Keep a loaded replay available when the pending live config is
            % invalid; a failed Reset must not destroy unrelated user data.
            if ~isempty(obj.replayData)
                obj.btnReplay.Enable = 'on';
                obj.btnReplay.Text = 'Replay animation';
            end
            obj.msg(['Cannot reset: ' ME.message]);
            obj.logMsg(['Configuration rejected: ' ME.message]);
            return;
        end
        obj.replayData = [];
        obj.btnReplay.Enable = 'off';
        obj.btnReplay.Text = 'Replay animation';
        obj.sldScrub.Enable = 'off';
        obj.realtimeBudget = 0;
        obj.pm.clearAll(); obj.v3d.reset(); obj.resetViewBounds();
        obj.dirtyNeedsReset = false;
        obj.refreshViews();
        obj.msg('Reset done.');
        obj.logMsg('Reset.');
    end

    function onStep(obj, src)
        src.Value = false;
        obj.playing = false;
        obj.replaying = false;
        hadReplayData = ~isempty(obj.replayData);
        needsConfigure = obj.dirtyNeedsReset || obj.engine.done;
        if needsConfigure
            try
                obj.engine.configure(obj.cfg);
            catch ME
                if hadReplayData
                    obj.btnReplay.Enable = 'on';
                    obj.btnReplay.Text = 'Replay animation';
                end
                obj.msg(['Cannot step: ' ME.message]);
                return;
            end
            obj.pm.clearAll(); obj.v3d.reset(); obj.resetViewBounds();
            obj.dirtyNeedsReset = false;
        elseif hadReplayData
            % Restore the paused engine's own trails rather than appending a
            % live sample to the previously loaded MAT visualization.
            obj.pm.clearAll(); obj.v3d.reset();
            try
                obj.v3d.setBounds(obj.engine.sampleTruth(200));
            catch ME
                obj.msg(['Could not restore live view: ' ME.message]);
                return;
            end
        end
        obj.replayData = [];
        obj.btnReplay.Enable = 'off';
        obj.btnReplay.Text = 'Replay animation';
        obj.realtimeBudget = 0;
        obj.engine.step();
        obj.refreshViews();
    end

    function onSpeed(obj, v)
        obj.cfg.Sim.speed = v;
        obj.lblSpeed.Text = sprintf('%.1fx', v);
    end

    function tick(obj)
        if obj.replaying
            obj.tickReplay();
            return;
        end
        if ~obj.playing, return; end
        if obj.engine.done
            obj.playing = false;
            obj.onFinished();
            return;
        end
        isFast = strcmp(obj.cfg.Sim.mode, 'fast');
        if isFast
            nStep = max(1, round(obj.cfg.Sim.chunkFast));
            obj.realtimeBudget = 0;
        else
            nStep = inf;
            % Carry one-step overshoot into the next timer callback.  A fixed
            % step count based on base dt made the two-rate mode run 2.5x too
            % fast because half of its intervals are 4*dt.
            obj.realtimeBudget = obj.realtimeBudget + obj.tmr.Period * obj.cfg.Sim.speed;
        end
        i = 0;
        while i < nStep && ~obj.engine.done && ...
                (isFast || obj.realtimeBudget > 1e-12)
            tBefore = obj.engine.t;
            prevEvt = obj.engine.gnssEvent;
            obj.engine.step();
            i = i + 1;
            if ~isFast
                obj.realtimeBudget = obj.realtimeBudget - (obj.engine.t - tBefore);
            end
            if ~strcmp(prevEvt, obj.engine.gnssEvent) && ...
                    strcmp(obj.engine.gnssEvent, 'DROPOUT')
                obj.logMsg('GNSS dropout (no measurement)');
            end
        end
        if obj.lastRefresh == 0 || toc(obj.lastRefresh) > 0.2
            obj.refreshViews();
            obj.lastRefresh = tic;
        end
    end

    function onFinished(obj)
        obj.msg('Simulation finished.');
        obj.logMsg('Simulation finished.');
        obj.refreshViews();
        d = obj.engine.log.slice();
        obj.txtLogInfo.Value = {sprintf('Samples: %d', d.n), ...
            sprintf('Duration: %.1f s', d.t(end)), ...
            sprintf('GNSS meas: %d', sum(~isnan(d.gnssFlag))), ...
            'Use Save MAT/CSV to export.'};
        obj.btnReplay.Enable = 'on';
        obj.autoSavePreset();
    end

    function refreshViews(obj)
        d = obj.engine.log.slice();
        obj.pm.setCfg(obj.cfg);
        obj.pm.update(d);
        obj.v3d.update(d);
        snap = obj.engine.getSnapshot();
        obj.dfv.update(snap);
        obj.lblTime.Text = sprintf('t = %.2f / %.0f s', obj.engine.t, obj.engine.cfg.Sim.duration);
        obj.lblPhase.Text = ['phase: ' obj.engine.phase];
        if obj.cfg.GNSS.enabled
            obj.lblGnss.Text = ['GNSS: ' obj.engine.gnssEvent];
        else
            obj.lblGnss.Text = 'GNSS: disabled';
        end
        if isfield(snap, 'err')
            obj.lblErr.Text = sprintf('|pos err| fused: %.2f m', snap.err.posFus);
        else
            obj.lblErr.Text = '|pos err| fused: -';
        end
        drawnow limitrate
    end

    % ============================================================ experiments
    function onExpSelect(obj, src)
        idx = find(strcmp(ExperimentPresets.list(), src.Value), 1);
        if isempty(idx), idx = 1; end
        txt = strrep(ExperimentPresets.description(idx), '\n', newline);
        obj.txtExpDesc.Value = strsplit(txt, newline)';
    end

    function idx = expIndex(obj)
        idx = find(strcmp(ExperimentPresets.list(), obj.ddExp.Value), 1);
    end

    function onExpApply(obj)
        idx = obj.expIndex();
        obj.playing = false;  % avoid running with a half-old/half-preset config
        obj.replaying = false;
        obj.btnReplay.Text = 'Replay animation';
        obj.cfg = ExperimentPresets.apply(obj.cfg, idx);
        obj.syncUI();
        obj.updateDirtyBadges();
        obj.dirtyNeedsReset = true;
        obj.msg(sprintf('Experiment %d applied. Press Start to watch.', idx));
        obj.logMsg(sprintf('Experiment %d applied to config.', idx));
    end

    function onExpRun(obj)
        idx = obj.expIndex();
        cla(obj.axExp); legend(obj.axExp, 'off');
        obj.msg('Running experiment headless...'); drawnow;
        cfgE = ExperimentPresets.apply(obj.cfg, idx);
        rows = {};
        hold(obj.axExp, 'on');
        try
        if idx == 15 || idx == 16
            obj.axExp.YScale = 'linear';
            if idx == 15
                obj.msg(sprintf('Monte Carlo: running 20 seeds...')); drawnow;
                r = MonteCarlo.run(cfgE, 20, 1000);
                MonteCarlo.plotCDF(r, obj.axExp);
                m = r.summary;
                rows = {'MC n=20 (current cfg)', m.meanRmsFus, m.p95FinFus, ...
                        m.meanFinFus, m.meanAttFus};
                obj.msg(sprintf('Monte Carlo done: mean final err %.2f m, p95 %.2f m.', ...
                    m.meanFinFus, m.p95FinFus));
            else
                obj.msg(sprintf('Monte Carlo: running 2x20 seeds (INS vs loose)...')); drawnow;
                r1 = MonteCarlo.run(cfgE, 20, 1000);
                cfgL = cfgE; cfgL.Fusion.mode = 'loose';
                r2 = MonteCarlo.run(cfgL, 20, 1000);
                MonteCarlo.plotCDF2(r1, r2, obj.axExp);
                rows = {'16a INS Only (20 runs)', r1.summary.meanRmsIns, r1.summary.p95FinFus, ...
                        r1.summary.meanFinFus, r1.summary.meanAttFus; ...
                        '16b GNSS/INS (20 runs)', r2.summary.meanRmsFus, r2.summary.p95FinFus, ...
                        r2.summary.meanFinFus, r2.summary.meanAttFus};
                obj.msg(sprintf('Monte Carlo done: INS p95 %.1f m vs Fused p95 %.2f m.', ...
                    r1.summary.p95FinFus, r2.summary.p95FinFus));
            end
            obj.tblExp.Data = [obj.tblExpData(); rows];
            obj.logMsg(sprintf('Monte Carlo experiment %d finished.', idx));
            return;
        elseif idx == 8
            r1 = ExperimentPresets.runHeadless(cfgE);
            cfgE.Fusion.mode = 'loose';
            r2 = ExperimentPresets.runHeadless(cfgE);
            m1 = ExperimentPresets.metrics(r1);
            m2 = ExperimentPresets.metrics(r2);
            rows = {'8a INS Only', m1.rmsPosFus, m1.maxPosFus, m1.finPosFus, m1.rmsAttDegF; ...
                    '8b GNSS/INS', m2.rmsPosFus, m2.maxPosFus, m2.finPosFus, m2.rmsAttDegF};
            obj.plotErr(r1, 'INS Only', [0.2 0.45 0.85]);
            obj.plotErr(r2, 'GNSS/INS', [0.05 0.6 0.25]);
            legend(obj.axExp, 'show');
            obj.msg('Experiment 8 done: INS Only vs GNSS/INS.');
        else
            obj.axExp.YScale = 'log';
            r = ExperimentPresets.runHeadless(cfgE);
            m = ExperimentPresets.metrics(r);
            rows = {sprintf('Exp %d', idx), m.rmsPosFus, m.maxPosFus, m.finPosFus, m.rmsAttDegF};
            obj.plotErr(r, sprintf('Exp %d fused', idx), [0.05 0.6 0.25]);
            obj.plotErrIns(r, sprintf('Exp %d INS', idx), [0.2 0.45 0.85]);
            legend(obj.axExp, 'show');
            obj.msg(sprintf('Experiment %d done.', idx));
        end
        catch ME
            obj.msg(['Experiment failed: ' ME.message]);
            obj.logMsg(['Experiment failed: ' ME.message]);
            return;
        end
        cur = obj.tblExpData();
        if isempty(cur), cur = {}; end
        obj.tblExp.Data = [cur; rows];
        obj.logMsg(sprintf('Experiment %d finished (headless).', idx));
    end

    function cur = tblExpData(obj)
        % uitable returns a table or {} depending on content; normalize.
        d = obj.tblExp.Data;
        if isempty(d), cur = {}; return; end
        if istable(d)
            cur = cell(d);
        else
            cur = d;
        end
    end

    function plotErr(obj, res, nm, c)
        idx = 1:max(1, floor(res.n/2000)):res.n;
        plot(obj.axExp, res.t(idx), res.errPosFus(idx) + 1e-6, 'Color', c, ...
            'LineWidth', 1.4, 'DisplayName', nm);
    end

    function plotErrIns(obj, res, nm, c)
        idx = 1:max(1, floor(res.n/2000)):res.n;
        plot(obj.axExp, res.t(idx), res.errPosIns(idx) + 1e-6, '--', 'Color', c, ...
            'LineWidth', 1.0, 'DisplayName', nm);
    end

    % ============================================================ logging/replay
    function onSaveMat(obj)
        [f, p] = uiputfile('navlog.mat', 'Save log (MAT)');
        if isequal(f, 0), return; end
        obj.engine.log.saveMAT(fullfile(p, f));
        obj.logMsg(['Saved MAT: ' f]);
    end

    function onSaveCsv(obj)
        [f, p] = uiputfile('navlog.csv', 'Save log (CSV)');
        if isequal(f, 0), return; end
        obj.engine.log.saveCSV(fullfile(p, f));
        obj.logMsg(['Saved CSV: ' f]);
    end

    function onLoadMat(obj)
        [f, p] = uigetfile('*.mat', 'Load log');
        if isequal(f, 0), return; end
        try
            s = load(fullfile(p, f));
        catch ME
            obj.msg(['Could not load MAT file: ' ME.message]);
            return;
        end
        if ~isfield(s, 'd')
            obj.msg('Not a NavSim log file (missing struct ''d'').');
            return;
        end
        try
            obj.replayData = obj.postProcessLoaded(s.d);
        catch ME
            obj.msg(['Invalid NavSim log: ' ME.message]);
            return;
        end
        obj.playing = false;
        obj.replaying = false;
        obj.btnReplay.Text = 'Replay animation';
        obj.pm.clearAll(); obj.v3d.reset();
        obj.v3d.setBounds(obj.replayData.truthP);
        obj.pm.update(obj.replayData);
        obj.v3d.update(obj.replayData);
        obj.btnReplay.Enable = 'on';
        obj.sldScrub.Enable = 'on';
        obj.sldScrub.Value = 1;
        obj.msg(['Loaded ' f ' — press Replay animation.']);
    end

    function d = postProcessLoaded(~, d)
        if ~isstruct(d)
            error('log payload ''d'' is not a struct');
        end
        vec3 = {'truthP','truthV','truthE','insP','insV','insE', ...
                'fusP','fusV','fusE','gnssP','gnssV','gyroT','gyroM', ...
                'accT','accM','alignEst'};
        if ~isfield(d, 't') || ~isnumeric(d.t) || isempty(d.t)
            error('missing or empty numeric time vector');
        end
        n = numel(d.t);
        if any(~isfinite(d.t(:))) || any(diff(d.t(:)) < 0)
            error('time vector must be finite and nondecreasing');
        end
        for i = 1:numel(vec3)
            fn = vec3{i};
            if ~isfield(d, fn) || ~isnumeric(d.(fn)) || ~isequal(size(d.(fn)), [3 n])
                error('field %s must have size 3-by-%d', fn, n);
            end
        end
        if any(~isfinite(d.truthP(:))) || any(~isfinite(d.truthV(:))) || ...
                any(~isfinite(d.truthE(:)))
            error('truth position/velocity/attitude must be finite');
        end
        if ~isfield(d, 'gnssFlag') || ~isnumeric(d.gnssFlag) || numel(d.gnssFlag) ~= n
            error('field gnssFlag must contain %d samples', n);
        end
        d.t = reshape(d.t, 1, []);
        d.gnssFlag = reshape(d.gnssFlag, 1, []);
        d.n = n;
        d.errPosFus = sqrt(sum((d.fusP - d.truthP).^2, 1));
        d.errPosIns = sqrt(sum((d.insP - d.truthP).^2, 1));
    end

    function onReplayToggle(obj)
        if isempty(obj.replayData)
            d = obj.engine.log.slice();
            if d.n < 2, return; end
            obj.replayData = obj.postProcessLoaded(d);
        end
        if obj.replaying
            obj.replaying = false;
            obj.btnReplay.Text = 'Replay animation';
        else
            obj.playing = false;
            obj.replaying = true;
            obj.replayIdx = 1;
            obj.v3d.reset();
            obj.v3d.update(obj.subSlice(obj.replayData, 1));
            obj.btnReplay.Text = 'Stop replay';
            if ~strcmp(obj.tmr.Running, 'on'), start(obj.tmr); end
        end
    end

    function tickReplay(obj)
        d = obj.replayData;
        targetTime = d.t(obj.replayIdx) + obj.tmr.Period * obj.cfg.Sim.speed;
        j = find(d.t >= targetTime, 1, 'first');
        if isempty(j), j = d.n; end
        obj.replayIdx = min(d.n, max(obj.replayIdx + 1, j));
        sub = obj.subSlice(d, obj.replayIdx);
        obj.v3d.update(sub);
        obj.lblTime.Text = sprintf('replay t = %.1f s', d.t(min(obj.replayIdx, d.n)));
        if obj.replayIdx >= d.n
            obj.replaying = false;
            obj.btnReplay.Text = 'Replay animation';
        end
        drawnow limitrate
    end

    function updateDirtyBadges(obj)
        % Mark every parameter label that differs from defaultConfig().
        def = defaultConfig();
        ks = keys(obj.labels);
        for i = 1:numel(ks)
            tag = ks{i};
            if ~isKey(obj.controls, tag), continue; end
            try
                cur = getByPath(obj.cfg, tag);
                defv = getByPath(def, tag);
            catch
                continue;
            end
            changed = ~valueEq(cur, defv);
            llst = obj.labels(tag);
            blst = obj.baseLabel(tag);
            clst = obj.baseColor(tag);
            for j = 1:numel(llst)
                if changed
                    llst{j}.Text = [blst{j} '  \u2260'];
                    llst{j}.FontColor = [0.85 0.45 0.0];
                else
                    llst{j}.Text = blst{j};
                    llst{j}.FontColor = clst{j};
                end
            end
        end
    end

    function tf = valueEq(a, b)
        if islogical(a) || islogical(b)
            tf = isequal(logical(a), logical(b));
        elseif isnumeric(a) && isnumeric(b)
            tf = isequal(size(a), size(b)) && ...
                max(abs(a(:) - b(:))) <= 1e-12 * max(1, max(abs(b(:))));
        elseif ischar(a) || isstring(a)
            tf = strcmp(char(a), char(b));
        else
            tf = isequal(a, b);
        end
    end

    function onSavePreset(obj)
        [f, p] = uiputfile('preset.mat', 'Save config preset (MAT)');
        if isequal(f, 0), return; end
        save(fullfile(p, f), 'cfg', '-v7');
        obj.logMsg(['Saved config preset: ' f]);
    end

    function onLoadPreset(obj)
        [f, p] = uigetfile('*.mat', 'Load config preset');
        if isequal(f, 0), return; end
        try
            s = load(fullfile(p, f), 'cfg');
        catch ME
            obj.msg(['Could not load preset: ' ME.message]);
            return;
        end
        if ~isfield(s, 'cfg')
            obj.msg('Not a NavSim config preset (missing cfg).');
            return;
        end
        try
            s.cfg = validateConfig(s.cfg);
        catch ME
            obj.msg(['Preset rejected: ' ME.message]);
            return;
        end
        obj.playing = false;
        obj.cfg = s.cfg;
        obj.syncUI();
        obj.updateDirtyBadges();
        obj.dirtyNeedsReset = true;
        obj.msg(['Loaded preset ' f ' — press Start to run it.']);
        obj.logMsg(['Loaded config preset: ' f]);
    end

    function onScrub(obj, v)
        if isempty(obj.replayData), return; end
        d = obj.replayData;
        i = max(1, min(d.n, 1 + round(v * (d.n - 1))));
        obj.pm.update(obj.scrubSlice(d, i));
        obj.lblScrub.Text = sprintf('scrub t = %.1f s', d.t(min(i, d.n)));
    end

    function sub = scrubSlice(~, d, i)
        sub = d; sub.n = i;
        f3 = {'truthP','truthV','truthE','insP','insV','insE','fusP','fusV','fusE', ...
              'gnssP','gnss2P','gnssV','calBg','calBa','gyroT','gyroM','accT','accM', ...
              'alignEst','sigP','sigV','sigA','errPosFus','errPosIns'};
        for k = 1:numel(f3)
            fn = f3{k};
            if isfield(d, fn) && size(d.(fn), 2) >= i
                tmp = d.(fn);
                sub.(fn) = tmp(:, 1:i);
            end
        end
        f1 = {'t','dt','gnssFlag','gnss2Flag','gnssTMeas','gnssOosm','innovN','nis', ...
              'gnssAccepted','oosmCount','baroH','baroFlag','zupt'};
        for k = 1:numel(f1)
            fn = f1{k};
            if isfield(d, fn) && numel(d.(fn)) >= i
                tmp = d.(fn);
                sub.(fn) = tmp(1:i);
            end
        end
    end

    function autoSavePreset(obj)
        % Auto-save the current config so a run can always be reproduced.
        try
            p = fullfile(fileparts(mfilename('fullpath')), 'presets');
            if ~exist(p, 'dir'), mkdir(p); end
            stamp = strrep(char(now('yyyymmdd_HHMMSS')), ' ', '_');
            f = fullfile(p, ['auto_' stamp '.mat']);
            save(f, 'cfg', '-v7');
            obj.logMsg(['Auto-saved config preset: ' f]);
        catch
            % never block the user flow because of preset saving
        end
    end

    function sub = subSlice(~, d, i)
        sub = d;
        sub.n = i;
        f3 = {'truthP','truthV','truthE','insP','insV','insE','fusP','fusV','fusE', ...
              'gnssP','gnssV','gyroT','gyroM','accT','accM','alignEst','errPosFus','errPosIns'};
        for k = 1:numel(f3)
            fn = f3{k};
            if isfield(d, fn) && size(d.(fn), 2) >= i
                values = d.(fn);
                sub.(fn) = values(:, 1:i);
            end
        end
        sub.t = d.t(1:i);
        if isfield(d, 'gnssFlag'), sub.gnssFlag = d.gnssFlag(1:i); end
    end

    function closeApp(obj)
        try
            if strcmp(obj.tmr.Running, 'on'), stop(obj.tmr); end
            delete(obj.tmr);
        catch
        end
        delete(obj.Fig);
    end
end
end
