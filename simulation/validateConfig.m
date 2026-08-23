function cfg = validateConfig(cfg)
%VALIDATECONFIG Fail early with actionable errors for unsafe core settings.
% The GUI constrains the same values, but headless callers can construct cfg
% structs directly and therefore need validation at the engine boundary.

required = {'Sim','Traj','IMU','GNSS','INS','Align','Fusion'};
for i = 1:numel(required)
    if ~isfield(cfg, required{i}) || ~isstruct(cfg.(required{i}))
        error('NavSim:InvalidConfig', 'Missing config section: %s', required{i});
    end
end

% Backward compatibility: configs saved before a feature existed keep
% working; missing fields fall back to the same disabled-by-default values
% used by defaultConfig.
gnssDefaults = struct('useGmNoise',false,'gmSigma',2,'gmTau',30,'outlierVelSigma',0);
fusionDefaults = struct('nisGateBaro',10.83,'useZupt',false, ...
    'zuptAccelG',0.05,'zuptRateDps',3,'zuptHoldS',1,'zuptSigma',0.05);
defaultsList = {gnssDefaults, 'GNSS'; fusionDefaults, 'Fusion'};
for i = 1:size(defaultsList, 1)
    sec = defaultsList{i, 2};
    fn = fieldnames(defaultsList{i, 1});
    for j = 1:numel(fn)
        if ~isfield(cfg.(sec), fn{j})
            cfg.(sec).(fn{j}) = defaultsList{i, 1}.(fn{j});
        end
    end
end

mustScalar(cfg.Sim.dt, 'Sim.dt', 0, inf, false);
mustScalar(cfg.Sim.duration, 'Sim.duration', 0, inf, false);
if cfg.Sim.dt <= 0 || cfg.Sim.duration <= 0
    error('NavSim:InvalidConfig', 'Sim.dt and Sim.duration must be greater than zero.');
end
mustScalar(cfg.Sim.speed, 'Sim.speed', 0, inf, false);
if cfg.Sim.speed <= 0
    error('NavSim:InvalidConfig', 'Sim.speed must be greater than zero.');
end
mustScalar(cfg.Sim.seed, 'Sim.seed', 0, 2^32-1, true);
mustScalar(cfg.Sim.dtJitter, 'Sim.dtJitter', 0, 0.9, false);
mustScalar(cfg.Sim.chunkFast, 'Sim.chunkFast', 1, inf, true);
mustChoice(cfg.Sim.mode, 'Sim.mode', {'realtime','fast'});
mustChoice(cfg.Sim.variableDt, 'Sim.variableDt', {'off','jitter','tworate'});

mustChoice(cfg.Traj.type, 'Traj.type', TrajectoryLibrary.list());
for f = {'speed','radius','alt0','climbRate','turnRate','heading0','accel'}
    mustScalar(cfg.Traj.(f{1}), ['Traj.' f{1}], -inf, inf, false);
end
if cfg.Traj.speed < 0 || cfg.Traj.radius <= 0 || cfg.Traj.alt0 < 0 || ...
        cfg.Traj.climbRate < 0 || cfg.Traj.accel < 0
    error('NavSim:InvalidConfig', ...
        'Trajectory speed/radius/altitude/climbRate/accel must be nonnegative (radius > 0).');
end
if ~(ischar(cfg.Traj.userExpr) || (isstring(cfg.Traj.userExpr) && isscalar(cfg.Traj.userExpr)))
    error('NavSim:InvalidConfig', 'Traj.userExpr must be text.');
end

mustScalar(cfg.GNSS.rate, 'GNSS.rate', 0, inf, false);
if cfg.GNSS.rate <= 0
    error('NavSim:InvalidConfig', 'GNSS.rate must be greater than zero.');
end
switch cfg.Sim.variableDt
    case 'jitter'
        maxDt = cfg.Sim.dt * (1 + cfg.Sim.dtJitter);
    case 'tworate'
        maxDt = 4 * cfg.Sim.dt;
    otherwise
        maxDt = cfg.Sim.dt;
end
if cfg.GNSS.enabled && cfg.GNSS.rate > (1 / maxDt) * (1 + 1e-12)
    error('NavSim:InvalidConfig', ...
        'GNSS.rate (%.3g Hz) exceeds the minimum simulation polling rate (%.3g Hz).', ...
        cfg.GNSS.rate, 1/maxDt);
end
for f = {'posSigmaH','posSigmaV','velSigma','outlierMag','delay', ...
         'gmSigma','gmTau','outlierVelSigma'}
    mustScalar(cfg.GNSS.(f{1}), ['GNSS.' f{1}], 0, inf, false);
end
if cfg.GNSS.useGmNoise && cfg.GNSS.gmTau <= 0
    error('NavSim:InvalidConfig', ...
        'GNSS.gmTau must be greater than zero when GNSS.useGmNoise is enabled.');
end
mustScalar(cfg.GNSS.randDropProb, 'GNSS.randDropProb', 0, 1, false);
mustScalar(cfg.GNSS.outlierProb, 'GNSS.outlierProb', 0, 1, false);

if ~isfield(cfg, 'Baro') || ~isstruct(cfg.Baro)
    % Older configs predate baro aiding; default it to disabled.
    cfg.Baro = struct('enabled',false,'rate',10,'sigma',1,'bias',0, ...
                      'gmSigma',0,'gmTau',60);
end
mustScalar(cfg.Baro.rate, 'Baro.rate', 0, inf, false);
if cfg.Baro.rate <= 0
    error('NavSim:InvalidConfig', 'Baro.rate must be greater than zero.');
end
for f = {'sigma','bias','gmSigma','gmTau'}
    mustScalar(cfg.Baro.(f{1}), ['Baro.' f{1}], 0, inf, false);
end
if cfg.Baro.gmSigma > 0 && cfg.Baro.gmTau <= 0
    error('NavSim:InvalidConfig', ...
        'Baro.gmTau must be greater than zero when Baro.gmSigma is positive.');
end
if cfg.Baro.enabled && cfg.Baro.rate > (1 / maxDt) * (1 + 1e-12)
    error('NavSim:InvalidConfig', ...
        'Baro.rate (%.3g Hz) exceeds the minimum simulation polling rate (%.3g Hz).', ...
        cfg.Baro.rate, 1/maxDt);
end
mustScalar(cfg.INS.gravity, 'INS.gravity', 0, inf, false);
if cfg.INS.gravity <= 0
    error('NavSim:InvalidConfig', 'INS.gravity must be greater than zero.');
end
mustScalar(cfg.INS.refLat, 'INS.refLat', -90, 90, false);
if abs(cfg.INS.refLat) >= 90
    error('NavSim:InvalidConfig', 'INS.refLat must be strictly between -90 and 90 degrees.');
end
mustScalar(cfg.INS.refLon, 'INS.refLon', -180, 180, false);
mustScalar(cfg.INS.refH, 'INS.refH', -inf, inf, false);
mustChoice(cfg.INS.earthModel, 'INS.earthModel', {'flat','wgs84'});

mustScalar(cfg.Align.duration, 'Align.duration', 0, inf, false);
mustScalar(cfg.Align.magHeadingSigmaDeg, 'Align.magHeadingSigmaDeg', 0, inf, false);
mustScalar(cfg.Align.coarseMovingSigmaDeg, 'Align.coarseMovingSigmaDeg', 0, inf, false);

mustChoice(cfg.Fusion.mode, 'Fusion.mode', {'ins','loose'});
mustChoice(cfg.Fusion.robustMode, 'Fusion.robustMode', {'off','reject','adaptive'});
for f = {'qa','qg','qbg','qba'}
    mustScalar(cfg.Fusion.(f{1}), ['Fusion.' f{1}], 0, inf, false);
end
for f = {'p0pos','p0vel','p0attDeg','p0gyroBiasDps','p0accelBias','qScale','rScale', ...
        'nisGatePos','nisGateVel','maxRInflation'}
    mustScalar(cfg.Fusion.(f{1}), ['Fusion.' f{1}], 0, inf, false);
    if cfg.Fusion.(f{1}) == 0
        error('NavSim:InvalidConfig', '%s must be greater than zero.', ['Fusion.' f{1}]);
    end
end
mustScalar(cfg.Fusion.oosmLag, 'Fusion.oosmLag', 0, inf, false);
if cfg.Fusion.useOOSM && cfg.Fusion.oosmLag <= 0
    error('NavSim:InvalidConfig', 'Fusion.oosmLag must be greater than zero when OOSM is enabled.');
end
mustScalar(cfg.Fusion.nisGateBaro, 'Fusion.nisGateBaro', 0, inf, false);
if cfg.Fusion.nisGateBaro == 0
    error('NavSim:InvalidConfig', 'Fusion.nisGateBaro must be greater than zero.');
end
for f = {'zuptAccelG','zuptRateDps','zuptHoldS','zuptSigma'}
    mustScalar(cfg.Fusion.(f{1}), ['Fusion.' f{1}], 0, inf, false);
end
if cfg.Fusion.useZupt
    if cfg.Fusion.zuptAccelG == 0 || cfg.Fusion.zuptRateDps == 0 || ...
            cfg.Fusion.zuptSigma == 0
        error('NavSim:InvalidConfig', ...
            'Fusion.zuptAccelG/zuptRateDps/zuptSigma must be greater than zero when ZUPT is enabled.');
    end
end
mustChoice(cfg.IMU.biasModel, 'IMU.biasModel', {'randomwalk','gaussmarkov'});
for f = {'gyroBiasTau','accelBiasTau','gyroSaturationDps','accelSaturationG'}
    mustScalar(cfg.IMU.(f{1}), ['IMU.' f{1}], 0, inf, false);
    if cfg.IMU.(f{1}) == 0
        error('NavSim:InvalidConfig', '%s must be greater than zero.', ['IMU.' f{1}]);
    end
end
for f = {'gyroQuantizationDps','accelQuantization'}
    mustScalar(cfg.IMU.(f{1}), ['IMU.' f{1}], 0, inf, false);
end

vectors = { ...
    cfg.IMU.gyroBiasDps, 'IMU.gyroBiasDps';
    cfg.IMU.gyroSFPpm, 'IMU.gyroSFPpm';
    cfg.IMU.gyroMisDeg, 'IMU.gyroMisDeg';
    cfg.IMU.accelBiasMg, 'IMU.accelBiasMg';
    cfg.IMU.accelSFPpm, 'IMU.accelSFPpm';
    cfg.IMU.accelMisDeg, 'IMU.accelMisDeg';
    cfg.GNSS.biasNed, 'GNSS.biasNed';
    cfg.INS.initPosErr, 'INS.initPosErr';
    cfg.INS.initVelErr, 'INS.initVelErr';
    cfg.Align.userErrDeg, 'Align.userErrDeg';
    cfg.IMU.gyroGSensitivity, 'IMU.gyroGSensitivity'};
for i = 1:size(vectors,1)
    v = vectors{i,1};
    if ~isnumeric(v) || numel(v) ~= 3 || any(~isfinite(v(:)))
        error('NavSim:InvalidConfig', '%s must be a finite 3-element numeric vector.', vectors{i,2});
    end
end

bools = { ...
    cfg.IMU.useGyroBias, 'IMU.useGyroBias'; cfg.IMU.useGyroNoise, 'IMU.useGyroNoise';
    cfg.IMU.useGyroSF, 'IMU.useGyroSF'; cfg.IMU.useGyroMis, 'IMU.useGyroMis';
    cfg.IMU.useAccelBias, 'IMU.useAccelBias'; cfg.IMU.useAccelNoise, 'IMU.useAccelNoise';
    cfg.IMU.useAccelSF, 'IMU.useAccelSF'; cfg.IMU.useAccelMis, 'IMU.useAccelMis';
    cfg.GNSS.enabled, 'GNSS.enabled'; cfg.GNSS.useNoise, 'GNSS.useNoise';
    cfg.GNSS.enableVel, 'GNSS.enableVel'; cfg.GNSS.useDropout, 'GNSS.useDropout';
    cfg.GNSS.useOutlier, 'GNSS.useOutlier'; cfg.Align.enabled, 'Align.enabled';
    cfg.Align.coarseLevel, 'Align.coarseLevel'; cfg.Align.applyUserErr, 'Align.applyUserErr';
    cfg.INS.useEarthRate, 'INS.useEarthRate';
    cfg.INS.useTransportRate, 'INS.useTransportRate';
    cfg.INS.useCoriolis, 'INS.useCoriolis';
    cfg.INS.useConingSculling, 'INS.useConingSculling';
    cfg.Fusion.useVel, 'Fusion.useVel'; cfg.Fusion.useOOSM, 'Fusion.useOOSM'; ...
    cfg.GNSS.useGmNoise, 'GNSS.useGmNoise'; cfg.Baro.enabled, 'Baro.enabled'; ...
    cfg.Fusion.useZupt, 'Fusion.useZupt'};
for i = 1:size(bools,1)
    v = bools{i,1};
    if ~(islogical(v) && isscalar(v)) && ...
            ~(isnumeric(v) && isscalar(v) && isfinite(v) && (v == 0 || v == 1))
        error('NavSim:InvalidConfig', '%s must be a scalar logical value.', bools{i,2});
    end
end

for f = {'gyroARWDpsHz','gyroBiasRW','accelVRW','accelBiasRW'}
    mustScalar(cfg.IMU.(f{1}), ['IMU.' f{1}], 0, inf, false);
end
end

function mustScalar(v, name, lo, hi, integerOnly)
if ~isnumeric(v) || ~isscalar(v) || ~isfinite(v) || v < lo || v > hi
    error('NavSim:InvalidConfig', '%s must be a finite scalar in [%g, %g].', name, lo, hi);
end
if integerOnly && v ~= fix(v)
    error('NavSim:InvalidConfig', '%s must be an integer.', name);
end
end

function mustChoice(v, name, choices)
if isstring(v) && isscalar(v), v = char(v); end
if ~ischar(v) || ~any(strcmp(v, choices))
    error('NavSim:InvalidConfig', '%s must be one of: %s.', name, strjoin(choices, ', '));
end
end
