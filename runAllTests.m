function runAllTests()
%RUNALLTESTS Numerical validation suite (no GUI required).
% Run from anywhere after startup.m has been executed (or run in NavSim root).

if isempty(which('SimEngine'))
    startup();
end

here = fileparts(mfilename('fullpath'));
testFiles = { ...
    'test_utils.m', ...
    'test_high_fidelity.m', ...
    'test_advanced_imu.m', ...
    'test_robust_oosm.m', ...
    'test_aiding.m', ...
    'test_perfect_match.m', ...
    'test_ins_drift.m', ...
    'test_ekf_convergence.m', ...
    'test_alignment.m', ...
    'test_variable_dt.m', ...
    'test_gnss_dropout.m', ...
    'test_time_alignment.m', ...
    'test_trajectory.m', ...
    'test_runtime_updates.m'};

nPass = 0; nFail = 0; failures = {};
fprintf('============================================================\n');
fprintf(' NavSim numerical validation suite\n');
fprintf('============================================================\n');
for i = 1:numel(testFiles)
    f = fullfile(here, 'tests', testFiles{i});
    [~, nm] = fileparts(f);
    try
        runOneTest(f);  % each script gets an isolated function workspace
        fprintf('  [PASS] %s\n', nm);
        nPass = nPass + 1;
    catch ME
        fprintf('  [FAIL] %s\n      %s\n', nm, ME.message);
        nFail = nFail + 1;
        failures{end+1} = nm; %#ok<AGROW>
    end
end
fprintf('------------------------------------------------------------\n');
fprintf(' Result: %d passed, %d failed\n', nPass, nFail);
if ~isempty(failures)
    disp(' Failed:'); disp(failures');
end
fprintf('============================================================\n');
if nFail > 0
    error('NavSim:TestsFailed', '%d validation test(s) failed.', nFail);
end
end

function runOneTest(f)
%RUNONETEST Keep script variables from leaking into subsequent tests.
run(f);
end
