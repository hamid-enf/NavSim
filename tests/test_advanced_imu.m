%TEST_ADVANCED_IMU Gauss-Markov, g-sensitivity, saturation and quantization.

c=defaultConfig();
for f={'useGyroBias','useGyroNoise','useGyroSF','useGyroMis', ...
       'useAccelBias','useAccelNoise','useAccelSF','useAccelMis'}
    c.IMU.(f{1})=false;
end
c.IMU.gyroGSensitivity=[1 2 3];          % deg/s/g, diagonal
c.IMU.gyroSaturationDps=10;
c.IMU.accelSaturationG=2;
c.IMU.gyroQuantizationDps=0.1;
c.IMU.accelQuantization=0.01;
im=IMUModel(); im.updateParams(c); im.reset();
[wm,fm,dbg]=im.measure(deg2rad([20;-20;0.14]),9.80665*[1;2;-1],0.1);
assert(max(abs(rad2deg(wm)-[10;-10;-2.9])) < 1e-10, ...
    'gyro g-sensitivity/saturation/quantization pipeline is incorrect');
assert(max(abs(fm-[9.81;19.61;-9.81])) < 1e-10, ...
    'accelerometer saturation/quantization pipeline is incorrect');
assert(dbg.gyroSaturated && ~dbg.accelSaturated, 'saturation diagnostics are incorrect');

% A first-order Gauss-Markov bias has an exact discrete transition and
% driving-noise standard deviation for each sample interval.
g=defaultConfig();
for f={'useGyroNoise','useGyroSF','useGyroMis','useAccelBias', ...
       'useAccelNoise','useAccelSF','useAccelMis'}
    g.IMU.(f{1})=false;
end
g.IMU.useGyroBias=true; g.IMU.gyroBiasDps=[0 0 0];
g.IMU.gyroBiasRW=0.02; g.IMU.biasModel='gaussmarkov'; g.IMU.gyroBiasTau=20;
g.IMU.gyroGSensitivity=[0 0 0]; g.IMU.gyroQuantizationDps=0;
dt=0.5; phi=exp(-dt/g.IMU.gyroBiasTau);
sigma=deg2rad(g.IMU.gyroBiasRW)*sqrt(0.5*g.IMU.gyroBiasTau*(1-phi^2));
rng(123,'twister'); expected=sigma*randn(3,1);
rng(123,'twister'); gm=IMUModel(); gm.updateParams(g); gm.reset();
[~,~,dgm]=gm.measure(zeros(3,1),zeros(3,1),dt);
assert(norm(dgm.bg-expected) < 1e-15, 'Gauss-Markov bias discretization is incorrect');

fprintf('  advanced IMU: g-sensitivity, limits, quantization and Gauss-Markov bias OK\n');
