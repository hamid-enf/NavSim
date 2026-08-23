function eulDot = bodyRates2eul(eul, w)
%BODYRATES2EUL Convert body rates [p;q;r] to Euler rates.
r = eul(1); th = eul(2);
p = w(1); q = w(2); s = w(3);
ct = max(cos(th), 1e-6);
eulDot = [ p + (q*sin(r) + s*cos(r))*tan(th);
           q*cos(r) - s*sin(r);
           (q*sin(r) + s*cos(r))/ct ];
end
