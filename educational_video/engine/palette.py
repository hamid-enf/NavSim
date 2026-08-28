"""Color palette and constants for the NavSim explainer video."""

W, H = 1920, 1080
FPS = 30

# background
BG_TOP = (13, 21, 42)
BG_BOT = (19, 30, 60)
GRID = (38, 52, 92)
PANEL = (19, 28, 51)
PANEL_EDGE = (40, 55, 95)
PANEL_SOFT = (24, 35, 66)

# text
TXT = (242, 246, 255)
TXT_DIM = (159, 176, 208)
TXT_FAINT = (110, 128, 165)

# stage colors
C_TRAJ = (148, 163, 184)
C_TRUTH = (248, 250, 252)
C_IMU = (245, 158, 11)
C_CALIB = (45, 212, 191)
C_INS = (56, 189, 248)
C_PRED = (129, 140, 248)
C_GNSS = (251, 146, 60)
C_FUSION = (52, 211, 153)
C_EST = (34, 211, 238)
C_ERR = (248, 113, 113)
C_BARO = (167, 139, 250)
C_ZUPT = (244, 114, 182)
C_OOSM = (251, 191, 36)
C_OK = (52, 211, 153)
C_WARN = (251, 191, 36)
C_BAD = (248, 113, 113)

STAGE_COLORS = {
    'Trajectory': C_TRAJ,
    'Truth': C_TRUTH,
    'IMU': C_IMU,
    'Calibration': C_CALIB,
    'INS': C_INS,
    'Prediction': C_PRED,
    'GNSS': C_GNSS,
    'Fusion': C_FUSION,
    'Estimate': C_EST,
    'Error': C_ERR,
    'Baro': C_BARO,
    'ZUPT': C_ZUPT,
    'OOSM': C_OOSM,
}

STAGES = ['Trajectory', 'Truth', 'IMU', 'Calibration', 'INS',
          'Prediction', 'GNSS', 'Fusion', 'Estimate', 'Error']
