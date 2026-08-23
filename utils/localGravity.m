function g = localGravity(cfg, h)
%LOCALGRAVITY Gravity magnitude (m/s^2). Constant model with optional
% free-air correction w.r.t. altitude above the reference (h = -D).
g0 = cfg.INS.gravity;
if nargin < 2 || isempty(h)
    g = g0;
else
    g = g0 - 3.086e-6 * h;   % simple free-air gradient
end
end
