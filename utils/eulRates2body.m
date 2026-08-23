function w = eulRates2body(eul, eulDot)
%EULRATES2BODY Convert Euler rates to body angular rates [p;q;r] (rad/s).
r = eul(1); th = eul(2);
rd = eulDot(1); thd = eulDot(2); yd = eulDot(3);
w = [ rd - yd*sin(th);
      thd*cos(r) + yd*sin(r)*cos(th);
     -thd*sin(r) + yd*cos(r)*cos(th) ];
end
