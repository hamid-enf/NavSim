classdef MonteCarlo
%MONTECARLO Headless seed-sweep runner: turns a single run into statistics.
%
%   r = MonteCarlo.run(cfg, nRuns, seedBase)
%       Runs SimEngine nRuns times with Sim.seed = seedBase .. seedBase+nRuns-1
%       (same config otherwise) and collects error metrics.
%
%   MonteCarlo.plotCDF(r, ax)          % fused vs INS-only CDF, one config
%   MonteCarlo.plotCDF2(rIns, rFus, ax) % two configs side by side
%
% No Statistics Toolbox required (percentiles computed manually).

methods (Static)
    function r = run(cfg, nRuns, seedBase)
        c = cfg;
        rmsFus = zeros(nRuns,1); finFus = zeros(nRuns,1);
        rmsIns = zeros(nRuns,1); attFus = zeros(nRuns,1);
        for i = 1:nRuns
            c.Sim.seed = seedBase + i - 1;
            eng = SimEngine(c);
            eng.runToEnd();
            res = eng.results();
            m = ExperimentPresets.metrics(res);
            rmsFus(i) = m.rmsPosFus;
            finFus(i) = m.finPosFus;
            rmsIns(i) = m.rmsPosIns;
            attFus(i) = m.rmsAttDegF;
        end
        r = struct('nRuns', nRuns, 'seedBase', seedBase, 'cfg', cfg, ...
            'rmsFus', rmsFus, 'finFus', finFus, ...
            'rmsIns', rmsIns, 'attFus', attFus, ...
            'summary', struct( ...
                'meanRmsFus', mean(rmsFus), ...
                'p95FinFus', pctl(finFus, 95), ...
                'meanFinFus', mean(finFus), ...
                'meanRmsIns', mean(rmsIns), ...
                'meanAttFus', mean(attFus)));
    end

    function plotCDF(r, ax)
        cla(ax); hold(ax, 'on'); grid(ax, 'on');
        y = (1:numel(r.finFus)) / numel(r.finFus);
        plot(ax, sort(r.finFus(:)), y, 'Color', [0.05 0.60 0.25], 'LineWidth', 1.8, ...
            'DisplayName', 'Fused: final |pos err| (CDF)');
        plot(ax, sort(r.rmsIns(:)), y, '--', 'Color', [0.20 0.45 0.85], 'LineWidth', 1.2, ...
            'DisplayName', 'INS only: rms |pos err| (CDF)');
        meanV = r.summary.meanRmsFus;
        yline(ax, 0.5, 'Color', [0.5 0.5 0.5], 'LineStyle', ':', 'LineWidth', 1);
        legend(ax, 'show', 'Location', 'best');
        xlabel(ax, '|pos err| [m]'); ylabel(ax, 'CDF');
        title(ax, sprintf('Monte Carlo: %d runs (seed %d)', r.nRuns, r.seedBase));
    end

    function plotCDF2(rIns, rFus, ax)
        cla(ax); hold(ax, 'on'); grid(ax, 'on');
        y = (1:numel(rIns.finFus)) / numel(rIns.finFus);
        plot(ax, sort(rIns.finFus(:)), y, '--', 'Color', [0.20 0.45 0.85], 'LineWidth', 1.4, ...
            'DisplayName', 'INS only: final |pos err| (CDF)');
        plot(ax, sort(rFus.finFus(:)), y, 'Color', [0.05 0.60 0.25], 'LineWidth', 1.8, ...
            'DisplayName', 'GNSS/INS: final |pos err| (CDF)');
        yline(ax, 0.5, 'Color', [0.5 0.5 0.5], 'LineStyle', ':', 'LineWidth', 1);
        legend(ax, 'show', 'Location', 'best');
        xlabel(ax, '|pos err| [m]'); ylabel(ax, 'CDF');
        title(ax, sprintf('Monte Carlo: %d runs each, INS vs GNSS/INS', rIns.nRuns));
    end

    function v = pctl(v, p)
        v = sort(v(:));
        v = v(v > 0 | true);   % keep zeros (perfect runs) too
        idx = max(1, ceil(p / 100 * numel(v)));
        v = v(idx);
    end
end
end
