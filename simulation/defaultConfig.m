function cfg = defaultConfig()
%DEFAULTCONFIG Full default configuration for the Navigation Simulator.
% All airflow-free SI units unless a field name documents its own unit.

% ---------------- Simulation engine ----------------
cfg.Sim.dt          = 0.01;       % IMU base step [s] (100 Hz)
cfg.Sim.duration    = 120;        % total duration [s]
cfg.Sim.speed       = 1;          % real-time speed multiplier (GUI)
cfg.Sim.mode        = 'realtime'; % 'realtime' | 'fast'
cfg.Sim.seed        = 1;          % RNG seed
cfg.Sim.variableDt  = 'off';      % 'off' | 'jitter' | 'tworate'
cfg.Sim.dtJitter    = 0.5;        % jitter magnitude (fraction of dt)
cfg.Sim.chunkFast   = 400;        % steps per GUI tick in fast mode

% ---------------- Trajectory ----------------
cfg.Traj.type       = 'Circle';
cfg.Traj.speed      = 15;         % [m/s]
cfg.Traj.radius     = 200;        % [m]
cfg.Traj.alt0       = 100;        % altitude above reference [m]
cfg.Traj.climbRate  = 3;          % [m/s]
cfg.Traj.turnRate   = 3;          % [deg/s]
cfg.Traj.heading0   = 0;          % [deg]
cfg.Traj.accel      = 1.5;        % [m/s^2] longitudinal acceleration
cfg.Traj.userExpr   = '[10*t; 100*sin(0.05*t); -100]'; % NED position [m]

% ---------------- IMU error model (true underlying errors) ----------------
cfg.IMU.useGyroBias   = true;
cfg.IMU.useGyroNoise  = true;
cfg.IMU.useGyroSF     = false;
cfg.IMU.useGyroMis    = false;
cfg.IMU.useAccelBias  = true;
cfg.IMU.useAccelNoise = true;
cfg.IMU.useAccelSF    = false;
cfg.IMU.useAccelMis   = false;
cfg.IMU.gyroBiasDps    = [0.02 -0.015 0.01];   % constant bias [deg/s]
cfg.IMU.gyroARWDpsHz   = 0.01;                 % angle random walk [deg/s/sqrt(Hz)]
cfg.IMU.gyroSFPpm      = [50 -30 20];          % scale factor [ppm]
cfg.IMU.gyroMisDeg     = [0.02 0.01 -0.015];   % misalignment [deg]
cfg.IMU.gyroBiasRW     = 0;                    % bias random walk [deg/s/sqrt(s)]
cfg.IMU.accelBiasMg    = [2 -1.5 1];           % constant bias [mg]
cfg.IMU.accelVRW       = 0.02;                 % velocity random walk [m/s/sqrt(Hz)]
cfg.IMU.accelSFPpm     = [80 40 -60];          % scale factor [ppm]
cfg.IMU.accelMisDeg    = [0.02 -0.02 0.01];    % misalignment [deg]
cfg.IMU.accelBiasRW    = 0;                    % bias driving noise [m/s^2/sqrt(s)]
% Higher-fidelity stochastic/instrument effects (zero/off preserves legacy data)
cfg.IMU.biasModel          = 'randomwalk';      % 'randomwalk' | 'gaussmarkov'
cfg.IMU.gyroBiasTau        = 3600;              % Gauss-Markov correlation time [s]
cfg.IMU.accelBiasTau       = 3600;              % Gauss-Markov correlation time [s]
cfg.IMU.gyroSaturationDps  = 400;               % symmetric gyro range [deg/s]
cfg.IMU.accelSaturationG   = 20;                % symmetric accelerometer range [g]
cfg.IMU.gyroQuantizationDps = 0;                % output LSB [deg/s], 0 disables
cfg.IMU.accelQuantization   = 0;                % output LSB [m/s^2], 0 disables
cfg.IMU.gyroGSensitivity    = [0 0 0];           % diagonal g-sensitivity [deg/s/g]

% ---------------- GNSS model ----------------
cfg.GNSS.enabled      = true;
cfg.GNSS.rate         = 1;         % update rate [Hz]
cfg.GNSS.useNoise     = true;
cfg.GNSS.posSigmaH    = 1.5;       % horizontal position sigma [m]
cfg.GNSS.posSigmaV    = 3.0;       % vertical position sigma [m]
cfg.GNSS.enableVel    = false;     % also output velocity measurement
cfg.GNSS.velSigma     = 0.05;      % velocity sigma [m/s]
cfg.GNSS.biasNed      = [0 0 0];   % constant bias N/E/D [m]
cfg.GNSS.useDropout   = false;
cfg.GNSS.dropoutText  = '60 75';   % outage windows: "t1 t2; t3 t4" [s]
cfg.GNSS.randDropProb = 0;         % per-epoch random dropout probability
cfg.GNSS.useOutlier   = false;
cfg.GNSS.outlierProb  = 0.02;      % per-epoch outlier probability
cfg.GNSS.outlierMag   = 50;        % outlier magnitude [m]
cfg.GNSS.outlierVelSigma = 0;      % outlier velocity error scale [m/s], 0 = off
cfg.GNSS.delay        = 0;         % measurement delay [s]
cfg.GNSS.useGmNoise   = false;     % Gauss-Markov correlated (multipath-like) error
cfg.GNSS.gmSigma      = 2;         % GM steady-state 1-sigma per axis [m]
cfg.GNSS.gmTau        = 30;        % GM correlation time [s]
% Satellite geometry -> time-varying DOP (off by default; keeps legacy noise)
cfg.GNSS.useSatGeometry = false;   % compute sigmaH/V from live HDOP/VDOP
cfg.GNSS.satCount       = 6;       % constellation size
cfg.GNSS.sig0           = 1.0;     % base code noise [m]; sigmaH = sig0*HDOP
cfg.GNSS.satPeriod      = 45;      % representative sky-rotation period [s] (accelerated)

% ---------------- Second GNSS receiver (dual-source aiding) ----------------
cfg.GNSS2.enabled     = false;    % feed a second receiver into the fusion
cfg.GNSS2.rate        = 1;        % update rate [Hz]
cfg.GNSS2.useNoise    = true;
cfg.GNSS2.posSigmaH   = 4.0;      % worse receiver on purpose (weighting demo)
cfg.GNSS2.posSigmaV   = 8.0;
cfg.GNSS2.enableVel   = false;
cfg.GNSS2.velSigma    = 0.1;
cfg.GNSS2.biasNed     = [0 0 0];
cfg.GNSS2.delay       = 0.5;      % typical network/delayed second receiver
%
% ---------------- Plot annotations ----------------
cfg.Plot.showSigmaBands      = true; % +/- sigma band around Fused position
cfg.Plot.showGnssAnnotations = true; % dropout windows + outlier markers
%
% ---------------- Barometric altimeter (altitude aiding) ----------------
cfg.Baro.enabled = false;   % feed altitude measurements into the fusion filter
cfg.Baro.rate    = 10;      % measurement rate [Hz]
cfg.Baro.sigma   = 1;       % white noise 1-sigma [m]
cfg.Baro.bias    = 0;       % constant bias [m]
cfg.Baro.gmSigma = 0;       % Gauss-Markov pressure-drift 1-sigma [m]
cfg.Baro.gmTau   = 60;      % GM correlation time [s]

% ---------------- INS ----------------
cfg.INS.gravity    = 9.80665;
cfg.INS.initPosErr = [0 0 0];      % initial position error N/E/D [m]
cfg.INS.initVelErr = [0 0 0];      % initial velocity error N/E/D [m/s]
cfg.INS.refLat     = 50.478;       % local NED reference geodetic point
cfg.INS.refLon     = 12.365;
cfg.INS.refH       = 430;
cfg.INS.earthModel = 'flat';      % 'flat' | 'wgs84' local-level mechanization
cfg.INS.useEarthRate = true;      % omega_ie in gyro/attitude dynamics (WGS84 mode)
cfg.INS.useTransportRate = true;  % omega_en from motion over the ellipsoid
cfg.INS.useCoriolis = true;       % (2*omega_ie + omega_en) x velocity
cfg.INS.useConingSculling = false;% off by default for flat-mode compatibility; selectable

% ---------------- Initial alignment ----------------
cfg.Align.enabled         = true;  % run an alignment phase before nav
cfg.Align.duration        = 10;    % alignment time [s]
cfg.Align.coarseLevel     = true;  % accelerometer levelling (roll/pitch)
cfg.Align.headingModel    = 'magnetometer'; % 'magnetometer' | 'gyrocompass' | 'magStub' (legacy)
cfg.Align.magDeclinationDeg = 5;   % magnetic declination at reference [deg]
cfg.Align.magFieldT       = 50e-6; % geomagnetic field strength F [T]
cfg.Align.magInclinationDeg = 60;  % magnetic inclination (dip) [deg]
cfg.Align.magNoiseT       = 4e-7;  % magnetometer noise 1-sigma [T] (~1 deg yaw)
cfg.Align.magBiasT        = 0;     % hard-iron bias magnitude [T]
cfg.Align.gyrocompassTau  = 15;    % gyrocompass effective tau [s] (accelerated; ~4.4e4 for real)
cfg.Align.magHeadingSigmaDeg = 1;  % magStub (legacy) yaw accuracy [deg]
cfg.Align.coarseMovingSigmaDeg = 3; % transfer-alignment coarse error [deg] (moving start)
cfg.Align.applyUserErr    = false; % add extra user-set initial error
cfg.Align.userErrDeg      = [0 0 5]; % extra initial [roll pitch yaw] error [deg]

% ---------------- Fusion (loosely-coupled error-state EKF) ----------------
cfg.Fusion.mode          = 'loose'; % 'ins' (INS only) | 'loose' (GNSS+INS)
cfg.Fusion.useVel        = false;   % use GNSS velocity updates if available
% Process noise spectral densities (tuning knobs)
cfg.Fusion.qa            = 0.05;    % accel noise density [m/s^2/sqrt(Hz)]
cfg.Fusion.qg            = 0.02;    % gyro noise density [deg/s/sqrt(Hz)]
cfg.Fusion.qbg           = 0.002;   % gyro bias RW [deg/s/sqrt(s)]
cfg.Fusion.qba           = 0.005;   % accel bias RW [m/s^2/sqrt(s)]
% Initial uncertainty (1-sigma)
cfg.Fusion.p0pos         = 5;       % [m]
cfg.Fusion.p0vel         = 0.5;     % [m/s]
cfg.Fusion.p0attDeg      = 5;       % [deg]
cfg.Fusion.p0gyroBiasDps = 0.5;     % [deg/s]
cfg.Fusion.p0accelBias   = 0.3;     % [m/s^2]
cfg.Fusion.qScale        = 1;       % process noise density multiplier
cfg.Fusion.rScale        = 1;       % measurement covariance multiplier
% Robust aiding and fixed-lag out-of-sequence measurement processing
cfg.Fusion.robustMode    = 'reject'; % 'off' | 'reject' | 'adaptive'
cfg.Fusion.nisGatePos    = 16.27;    % chi-square, 3 DOF (~99.9%)
cfg.Fusion.nisGateVel    = 16.27;
cfg.Fusion.maxRInflation = 100;      % adaptive-mode cap before rejection
cfg.Fusion.useOOSM       = true;
cfg.Fusion.oosmLag       = 12;       % retained fixed-lag history [s]
cfg.Fusion.nisGateBaro   = 10.83;    % chi-square, 1 DOF (~99.9%), baro altitude
% Zero-velocity updates (ZUPT) while the platform is detected stationary
cfg.Fusion.useZupt       = false;    % enable zero-velocity aiding
cfg.Fusion.zuptAccelG    = 0.05;     % |f|-magnitude stationarity gate [g]
cfg.Fusion.zuptRateDps   = 3;        % rate-magnitude stationarity gate [deg/s]
cfg.Fusion.zuptHoldS     = 1;        % stationarity hold time before firing [s]
cfg.Fusion.zuptSigma     = 0.05;     % assumed ZUPT velocity sigma [m/s]
end
