function startup()
%STARTUP Add Navigation Simulator folders to the MATLAB path.
root = fileparts(mfilename('fullpath'));
dirs = {'simulation','trajectory','imu','gnss','ins','fusion','alignment', ...
        'visualization','ui','logging','utils','tests'};
for i = 1:numel(dirs)
    addpath(fullfile(root, dirs{i}));
end
fprintf('NavSim: path initialized (%s)\n', root);
end
