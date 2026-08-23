function spec = ParamCatalog()
%PARAMCATALOG Spec-driven UI definition.
% Row format: {TabName, Label, ConfigPath, Type, Extra}
%   Type: 'num' | 'check' | 'drop' | 'text'
%   For 'drop', Extra = items cell array; for 'num', Extra = [min max step].

spec = {
% ---------------- Simulation ----------------
'Simulation','IMU dt [s]','Sim.dt','num',[0.002 0.05 0.001];
'Simulation','Duration [s]','Sim.duration','num',[5 3600 1];
'Simulation','RNG seed','Sim.seed','num',[0 1e6 1];
'Simulation','Run mode','Sim.mode','drop',{'realtime','fast'};
'Simulation','Fast chunk [steps/tick]','Sim.chunkFast','num',[10 20000 10];
'Simulation','Variable dt','Sim.variableDt','drop',{'off','jitter','tworate'};
'Simulation','dt jitter fraction','Sim.dtJitter','num',[0 0.9 0.05];
% ---------------- Trajectory ----------------
'Trajectory','Type','Traj.type','drop',TrajectoryLibrary.list();
'Trajectory','Speed [m/s]','Traj.speed','num',[0 400 0.5];
'Trajectory','Radius / scale [m]','Traj.radius','num',[10 5000 10];
'Trajectory','Altitude above ref [m]','Traj.alt0','num',[5 20000 5];
'Trajectory','Climb rate [m/s]','Traj.climbRate','num',[0 100 0.5];
'Trajectory','Turn rate [deg/s]','Traj.turnRate','num',[0.1 30 0.1];
'Trajectory','Initial heading [deg]','Traj.heading0','num',[-180 180 1];
'Trajectory','Accel (Acceleration traj) [m/s^2]','Traj.accel','num',[0 30 0.1];
'Trajectory','User expr p(t) (NED [m])','Traj.userExpr','text','';
% ---------------- IMU ----------------
'IMU','Enable gyro bias','IMU.useGyroBias','check','';
'IMU','Gyro bias X [deg/s]','IMU.gyroBiasDps(1)','num',[-10 10 0.001];
'IMU','Gyro bias Y [deg/s]','IMU.gyroBiasDps(2)','num',[-10 10 0.001];
'IMU','Gyro bias Z [deg/s]','IMU.gyroBiasDps(3)','num',[-10 10 0.001];
'IMU','Enable gyro noise','IMU.useGyroNoise','check','';
'IMU','Gyro ARW [deg/s/sqrtHz]','IMU.gyroARWDpsHz','num',[0 2 0.001];
'IMU','Gyro bias RW [deg/s/sqrts]','IMU.gyroBiasRW','num',[0 1 0.0001];
'IMU','Enable gyro scale factor','IMU.useGyroSF','check','';
'IMU','Gyro SF X [ppm]','IMU.gyroSFPpm(1)','num',[-5000 5000 10];
'IMU','Gyro SF Y [ppm]','IMU.gyroSFPpm(2)','num',[-5000 5000 10];
'IMU','Gyro SF Z [ppm]','IMU.gyroSFPpm(3)','num',[-5000 5000 10];
'IMU','Enable gyro misalignment','IMU.useGyroMis','check','';
'IMU','Gyro misalign X [deg]','IMU.gyroMisDeg(1)','num',[-2 2 0.005];
'IMU','Gyro misalign Y [deg]','IMU.gyroMisDeg(2)','num',[-2 2 0.005];
'IMU','Gyro misalign Z [deg]','IMU.gyroMisDeg(3)','num',[-2 2 0.005];
'IMU','Enable accel bias','IMU.useAccelBias','check','';
'IMU','Accel bias X [mg]','IMU.accelBiasMg(1)','num',[-500 500 0.5];
'IMU','Accel bias Y [mg]','IMU.accelBiasMg(2)','num',[-500 500 0.5];
'IMU','Accel bias Z [mg]','IMU.accelBiasMg(3)','num',[-500 500 0.5];
'IMU','Enable accel noise','IMU.useAccelNoise','check','';
'IMU','Accel VRW [m/s/sqrtHz]','IMU.accelVRW','num',[0 1 0.005];
'IMU','Accel bias RW [m/s2/sqrts]','IMU.accelBiasRW','num',[0 1 0.0001];
'IMU','Enable accel scale factor','IMU.useAccelSF','check','';
'IMU','Accel SF X [ppm]','IMU.accelSFPpm(1)','num',[-5000 5000 10];
'IMU','Accel SF Y [ppm]','IMU.accelSFPpm(2)','num',[-5000 5000 10];
'IMU','Accel SF Z [ppm]','IMU.accelSFPpm(3)','num',[-5000 5000 10];
'IMU','Enable accel misalignment','IMU.useAccelMis','check','';
'IMU','Accel misalign X [deg]','IMU.accelMisDeg(1)','num',[-2 2 0.005];
'IMU','Accel misalign Y [deg]','IMU.accelMisDeg(2)','num',[-2 2 0.005];
'IMU','Accel misalign Z [deg]','IMU.accelMisDeg(3)','num',[-2 2 0.005];
'IMU','Bias stochastic model','IMU.biasModel','drop',{'randomwalk','gaussmarkov'};
'IMU','Gyro bias correlation [s]','IMU.gyroBiasTau','num',[1 100000 10];
'IMU','Accel bias correlation [s]','IMU.accelBiasTau','num',[1 100000 10];
'IMU','Gyro saturation [deg/s]','IMU.gyroSaturationDps','num',[1 5000 10];
'IMU','Accel saturation [g]','IMU.accelSaturationG','num',[1 500 1];
'IMU','Gyro quantization [deg/s]','IMU.gyroQuantizationDps','num',[0 1 0.0001];
'IMU','Accel quantization [m/s2]','IMU.accelQuantization','num',[0 1 0.0001];
'IMU','Gyro g-sens X [deg/s/g]','IMU.gyroGSensitivity(1)','num',[-1 1 0.0001];
'IMU','Gyro g-sens Y [deg/s/g]','IMU.gyroGSensitivity(2)','num',[-1 1 0.0001];
'IMU','Gyro g-sens Z [deg/s/g]','IMU.gyroGSensitivity(3)','num',[-1 1 0.0001];
% ---------------- GNSS ----------------
'GNSS','GNSS enabled','GNSS.enabled','check','';
'GNSS','Update rate [Hz]','GNSS.rate','num',[0.1 50 0.5];
'GNSS','Enable GNSS noise','GNSS.useNoise','check','';
'GNSS','Pos sigma horizontal [m]','GNSS.posSigmaH','num',[0 100 0.1];
'GNSS','Pos sigma vertical [m]','GNSS.posSigmaV','num',[0 200 0.1];
'GNSS','Enable velocity output','GNSS.enableVel','check','';
'GNSS','Vel sigma [m/s]','GNSS.velSigma','num',[0 5 0.01];
'GNSS','Bias N [m]','GNSS.biasNed(1)','num',[-200 200 0.5];
'GNSS','Bias E [m]','GNSS.biasNed(2)','num',[-200 200 0.5];
'GNSS','Bias D [m]','GNSS.biasNed(3)','num',[-200 200 0.5];
'GNSS','Enable dropout','GNSS.useDropout','check','';
'GNSS','Dropout windows "t1 t2; t3 t4" [s]','GNSS.dropoutText','text','';
'GNSS','Random dropout prob (per epoch)','GNSS.randDropProb','num',[0 1 0.01];
'GNSS','Enable outliers','GNSS.useOutlier','check','';
'GNSS','Outlier probability','GNSS.outlierProb','num',[0 1 0.005];
'GNSS','Outlier magnitude [m]','GNSS.outlierMag','num',[0 500 5];
'GNSS','Measurement delay [s]','GNSS.delay','num',[0 10 0.1];
% ---------------- INS & Alignment ----------------
'INS & Align','Gravity [m/s^2]','INS.gravity','num',[9.7 9.9 0.00001];
'INS & Align','Init pos err N [m]','INS.initPosErr(1)','num',[-1000 1000 0.5];
'INS & Align','Init pos err E [m]','INS.initPosErr(2)','num',[-1000 1000 0.5];
'INS & Align','Init pos err D [m]','INS.initPosErr(3)','num',[-1000 1000 0.5];
'INS & Align','Init vel err N [m/s]','INS.initVelErr(1)','num',[-100 100 0.05];
'INS & Align','Init vel err E [m/s]','INS.initVelErr(2)','num',[-100 100 0.05];
'INS & Align','Init vel err D [m/s]','INS.initVelErr(3)','num',[-100 100 0.05];
'INS & Align','Ref latitude [deg]','INS.refLat','num',[-89.999 89.999 0.001];
'INS & Align','Ref longitude [deg]','INS.refLon','num',[-180 180 0.001];
'INS & Align','Ref altitude [m]','INS.refH','num',[-500 9000 10];
'INS & Align','Earth model','INS.earthModel','drop',{'flat','wgs84'};
'INS & Align','Include Earth rotation','INS.useEarthRate','check','';
'INS & Align','Include transport rate','INS.useTransportRate','check','';
'INS & Align','Include Coriolis','INS.useCoriolis','check','';
'INS & Align','Coning/sculling compensation','INS.useConingSculling','check','';
'INS & Align','Alignment enabled','Align.enabled','check','';
'INS & Align','Alignment duration [s]','Align.duration','num',[0 600 1];
'INS & Align','Coarse levelling (accel)','Align.coarseLevel','check','';
'INS & Align','Mag heading sigma [deg]','Align.magHeadingSigmaDeg','num',[0 20 0.1];
'INS & Align','Transfer-align coarse sigma [deg]','Align.coarseMovingSigmaDeg','num',[0 30 0.1];
'INS & Align','Apply extra initial error','Align.applyUserErr','check','';
'INS & Align','Init err roll [deg]','Align.userErrDeg(1)','num',[-45 45 0.1];
'INS & Align','Init err pitch [deg]','Align.userErrDeg(2)','num',[-45 45 0.1];
'INS & Align','Init err yaw [deg]','Align.userErrDeg(3)','num',[-180 180 0.1];
% ---------------- Fusion ----------------
'Fusion','Mode (ins | loose)','Fusion.mode','drop',{'ins','loose'};
'Fusion','Use GNSS velocity updates','Fusion.useVel','check','';
'Fusion','Q accel density [m/s^2/sqrtHz]','Fusion.qa','num',[0.0001 5 0.001];
'Fusion','Q gyro density [deg/s/sqrtHz]','Fusion.qg','num',[0.0001 2 0.001];
'Fusion','Q gyro-bias RW [deg/s/sqrts]','Fusion.qbg','num',[0 0.5 0.0005];
'Fusion','Q accel-bias RW [m/s^2/sqrts]','Fusion.qba','num',[0 0.5 0.0005];
'Fusion','P0 position sigma [m]','Fusion.p0pos','num',[0.01 1000 0.5];
'Fusion','P0 velocity sigma [m/s]','Fusion.p0vel','num',[0.001 100 0.05];
'Fusion','P0 attitude sigma [deg]','Fusion.p0attDeg','num',[0.01 90 0.1];
'Fusion','P0 gyro bias sigma [deg/s]','Fusion.p0gyroBiasDps','num',[0.0001 20 0.01];
'Fusion','P0 accel bias sigma [m/s^2]','Fusion.p0accelBias','num',[0.0001 10 0.01];
'Fusion','Process noise scale','Fusion.qScale','num',[0.01 100 0.01];
'Fusion','Measurement noise scale','Fusion.rScale','num',[0.01 100 0.01];
'Fusion','Robust innovation mode','Fusion.robustMode','drop',{'off','reject','adaptive'};
'Fusion','Position NIS gate (3 DOF)','Fusion.nisGatePos','num',[0.1 1000 0.1];
'Fusion','Velocity NIS gate (3 DOF)','Fusion.nisGateVel','num',[0.1 1000 0.1];
'Fusion','Max adaptive R inflation','Fusion.maxRInflation','num',[1 10000 1];
'Fusion','Fixed-lag delayed GNSS (OOSM)','Fusion.useOOSM','check','';
'Fusion','OOSM lag window [s]','Fusion.oosmLag','num',[0.1 120 0.1];
% ---------------- Errors (master toggles) ----------------
'Errors','Gyro bias','IMU.useGyroBias','check','';
'Errors','Accel bias','IMU.useAccelBias','check','';
'Errors','Gyro noise','IMU.useGyroNoise','check','';
'Errors','Accel noise','IMU.useAccelNoise','check','';
'Errors','Gyro scale factor','IMU.useGyroSF','check','';
'Errors','Accel scale factor','IMU.useAccelSF','check','';
'Errors','Gyro misalignment','IMU.useGyroMis','check','';
'Errors','Accel misalignment','IMU.useAccelMis','check','';
'Errors','GNSS noise','GNSS.useNoise','check','';
'Errors','GNSS outlier','GNSS.useOutlier','check','';
'Errors','GNSS dropout','GNSS.useDropout','check','';
'Errors','Initial alignment error','Align.applyUserErr','check','';
'Errors','Timing error (variable dt mode)','Sim.variableDt','drop',{'off','jitter','tworate'};
};
end
