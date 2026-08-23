classdef DataFlowView < handle
%DATAFLOWVIEW Live monitor of the whole data flow + educational panel.
% Click any stage button to see a short applied explanation.

properties
    panel
    txtVals
    eduTitle
    eduBody
    statusLbl
end

methods
    function build(obj, parent)
        g = uigridlayout(parent, [1 2]);
        g.ColumnWidth = {170, '1x'};

        % ---------------- stage buttons ----------------
        stages = EduContent.list();
        nRows = 1 + numel(stages) + (numel(stages)-1) + 2;
        gl = uigridlayout(g, [nRows 1]);
        gl.RowHeight = repmat({26}, 1, nRows);
        gl.Padding = [6 6 6 6]; gl.Scrollable = 'on';
        gl.BackgroundColor = [0.94 0.95 0.98];
        uilabel(gl, 'Text', 'DATA FLOW', 'FontWeight', 'bold', ...
            'HorizontalAlignment', 'center');
        for i = 1:numel(stages)
            st = stages{i};
            uibutton(gl, 'push', 'Text', st, ...
                'ButtonPushedFcn', @(~,~) obj.showEdu(st));
            if i < numel(stages)
                uilabel(gl, 'Text', char(8595), 'HorizontalAlignment', 'center');
            end
        end
        uibutton(gl, 'push', 'Text', 'Alignment', 'ButtonPushedFcn', @(~,~) obj.showEdu('Alignment'));
        uibutton(gl, 'push', 'Text', 'Transform', 'ButtonPushedFcn', @(~,~) obj.showEdu('Transform'));

        % ---------------- right side ----------------
        gr = uigridlayout(g, [3 1]);
        gr.RowHeight = {'1.2x', 26, '1x'};
        obj.txtVals = uitextarea(gr, 'Editable', 'off', ...
            'FontName', 'Courier New', 'FontSize', 11, ...
            'Value', {'(waiting for data...)'});
        obj.eduTitle = uilabel(gr, 'Text', 'Education: click a stage on the left', ...
            'FontWeight', 'bold', 'BackgroundColor', [0.9 0.93 1], 'FontColor', [0.1 0.2 0.5]);
        obj.eduBody = uitextarea(gr, 'Editable', 'off', 'FontSize', 11, ...
            'Value', {'Click any stage button (Trajectory, IMU, INS, ...) to learn', ...
                      'what it does, its inputs/outputs, equations and errors.'});
    end

    function showEdu(obj, stage)
        s = EduContent.get(stage);
        obj.eduTitle.Text = ['Education: ' s.title];
        obj.eduBody.Value = strsplit(s.body, newline)';
    end

    function update(obj, snap)
        if ~isfield(snap, 'truth'), return; end
        d2 = @(x) sprintf('%8.2f %8.2f %8.2f', x(1), x(2), x(3));
        v = {};
        v{end+1} = sprintf(' t = %7.2f s   phase = %s   dt = %.4f s', snap.t, snap.phase, snap.dt);
        v{end+1} = ' ';
        v{end+1} = 'TRUTH';
        v{end+1} = sprintf('   Pos NED [m]  : %s', d2(snap.truth.p));
        v{end+1} = sprintf('   Vel NED [m/s]: %s', d2(snap.truth.v));
        v{end+1} = sprintf('   Att r/p/y [deg]: %s', d2(rad2deg(snap.truth.eul)));
        lla = snap.truth.lla;
        v{end+1} = sprintf('   Lat/Lon/Alt : %.6f  %.6f  %7.1f', lla(1), lla(2), lla(3));
        v{end+1} = ' ';
        v{end+1} = 'IMU MEASUREMENT';
        v{end+1} = sprintf('   Gyro  [deg/s]: %s', d2(rad2deg(snap.imu.w)));
        v{end+1} = sprintf('   Accel [m/s2] : %s', d2(snap.imu.f));
        v{end+1} = sprintf('   bias est used[deg/s]: %s', d2(rad2deg(snap.calib.bgEst)));
        v{end+1} = sprintf('   accel bias est[m/s2]: %s', d2(snap.calib.baEst));
        v{end+1} = ' ';
        v{end+1} = 'INS OUTPUT';
        v{end+1} = sprintf('   Pos NED [m]: %s', d2(snap.insState.p));
        v{end+1} = sprintf('   Vel N[m/s]: %s', d2(snap.insState.v));
        v{end+1} = sprintf('   Att  [deg]: %s', d2(rad2deg(snap.insState.eul)));
        v{end+1} = ' ';
        if snap.gnss.enabled
            v{end+1} = sprintf('GNSS  (%s)', snap.gnss.event);
            v{end+1} = sprintf('   Pos NED [m]: %s', d2(snap.gnss.p));
        else
            v{end+1} = 'GNSS  (disabled)';
        end
        v{end+1} = ' ';
        v{end+1} = 'FILTER (PREDICTION) 1-sigma';
        v{end+1} = sprintf('   sig pos [m]  : %s', d2(snap.pred.sigP));
        v{end+1} = sprintf('   sig att [deg]: %s', d2(rad2deg(snap.pred.sigA)));
        v{end+1} = ' ';
        v{end+1} = 'FUSED OUTPUT';
        llf = snap.fused.lla;
        v{end+1} = sprintf('   Lat/Lon/Alt: %.6f  %.6f  %7.1f', llf(1), llf(2), llf(3));
        v{end+1} = ' ';
        v{end+1} = 'ERROR ANALYSIS';
        v{end+1} = sprintf('   |pos err| INS   : %8.3f m', snap.err.posIns);
        v{end+1} = sprintf('   |pos err| Fused : %8.3f m', snap.err.posFus);
        v{end+1} = sprintf('   |vel err| Fused : %8.3f m/s', snap.err.velFus);
        v{end+1} = sprintf('   |att err| Fused : %8.3f deg', snap.err.attFusDeg);
        obj.txtVals.Value = v;
    end
end
end
